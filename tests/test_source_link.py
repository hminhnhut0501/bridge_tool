import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

import httpx
from telethon import types

from scripts.audit_simulations import login, sandbox
from telegram_vault.api import create_app
from telegram_vault.providers import TelethonProvider


class SourceLinkTests(unittest.IsolatedAsyncioTestCase):
    async def test_public_private_and_invite_links_resolve_without_dialog_scan(self):
        async with sandbox() as c:
            p = TelethonProvider(c.config, c.engine.rate)
            p.status = "connected"
            group = types.Channel(
                id=123,
                title="Group",
                photo=types.ChatPhotoEmpty(),
                date=None,
                megagroup=True,
                forum=True,
            )
            p.client = SimpleNamespace(get_entity=AsyncMock(return_value=group))
            for link, expected in [
                ("https://t.me/example_group/42", "@example_group"),
                ("https://t.me/c/123/42", types.PeerChannel(123)),
            ]:
                source = await p.resolve_source(link)
                p.client.get_entity.assert_awaited_with(expected)
                self.assertEqual(source["chat_id"], -1000000000123)
                self.assertTrue(source["forum"])
            p.client = AsyncMock(return_value=types.ChatInviteAlready(chat=group))
            self.assertEqual((await p.resolve_source("https://t.me/+testhash"))["name"], "Group")
            p.client.return_value = types.ChatInvite(
                title="Other", color=0, photo=types.PhotoEmpty(id=1), participants_count=1
            )
            with self.assertRaisesRegex(ValueError, "chưa tham gia"):
                await p.resolve_source("https://t.me/+testhash")
            with self.assertRaises(ValueError):
                await p.resolve_source("https://example.com/group")

    async def test_direct_api_skips_discovery_and_creates_paused_source(self):
        async with sandbox() as c:
            c.provider.list_sources = AsyncMock(side_effect=AssertionError("must not scan dialogs"))
            app = create_app(c.config, c.engine)
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url=c.config.app_url
            ) as client:
                headers = await login(client)
                r = await client.post(
                    "/api/sources",
                    headers=headers,
                    json={
                        "reference": str(c.provider.groups[0]["chat_id"]),
                        "rights_confirmed": True,
                    },
                )
                self.assertEqual(r.status_code, 200, r.text)
                self.assertEqual(r.json()["paused"], 1)
                c.provider.list_sources.assert_not_awaited()

    async def test_channel_resolves_and_is_discovered_without_topics(self):
        async with sandbox() as c:
            p = TelethonProvider(c.config, c.engine.rate)
            p.status = "connected"
            channel = types.Channel(
                id=999, title="News", photo=types.ChatPhotoEmpty(), date=None, broadcast=True
            )
            p.client = SimpleNamespace(get_entity=AsyncMock(return_value=channel))
            source = await p.resolve_source("https://t.me/news_channel/42")
            self.assertEqual(source["kind"], "channel")
            self.assertFalse(source["forum"])
            self.assertEqual(source["chat_id"], -1000000000999)

            async def dialogs():
                yield SimpleNamespace(
                    is_group=False,
                    is_channel=True,
                    id=source["chat_id"],
                    name="News",
                    entity=channel,
                )

            p.client.iter_dialogs = dialogs
            self.assertEqual(await p.list_sources(), [source])
            c.engine.provider = p
            sid = await c.engine.add_source("https://t.me/news_channel")
            stored = c.db.one("SELECT * FROM sources WHERE id=?", (sid,))
            self.assertEqual(stored["kind"], "channel")
            self.assertEqual(stored["paused"], 1)
            self.assertEqual(stored["forum"], 0)
