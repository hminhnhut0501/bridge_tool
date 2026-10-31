import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram_vault.models import Message


class FilenameTests(unittest.TestCase):
    def test_album_and_single_format(self):
        date = datetime(2025, 10, 4, 12, tzinfo=ZoneInfo("Asia/Ho_Chi_Minh")).timestamp()
        source = dict(path_name="Group", forum=False)
        for index, extension in [(1, "mp4"), (2, "mp4"), (3, "jpg")]:
            message = Message(
                1,
                4820 + index,
                date,
                filename="TenFileGoc." + extension,
                album_id=4821,
                album_index=index,
                caption="CaptionNgan",
            )
            self.assertEqual(
                message.remote_path("Root", source, None),
                f"Root/Telegram/Group/251004_G4821-{index:02d}_TenFileGoc_CaptionNgan.{extension}",
            )
        message = Message(1, 4900, date + 86400, filename="TenFileGoc.pdf", caption="CaptionNgan")
        self.assertEqual(
            message.remote_path("Root", source, None),
            "Root/Telegram/Group/251005_M4900_TenFileGoc_CaptionNgan.pdf",
        )

    def test_local_day_sanitization_extension_and_no_caption(self):
        date = datetime(2025, 10, 4, 18, tzinfo=ZoneInfo("UTC")).timestamp()
        message = Message(1, 1, date, filename="test.MP4", caption="line1\nline2/invalid")
        path = message.remote_path(
            "Root", dict(path_name="Group", forum=True), dict(path_name="Topic")
        )
        self.assertTrue(path.startswith("Root/Telegram/Group/Topic/251005_M1_test_"))
        self.assertEqual(path.count("/"), 4)
        self.assertTrue(path.endswith(".mp4"))


class AlbumMetadataTests(unittest.IsolatedAsyncioTestCase):
    async def test_unnamed_media_preserves_type_and_extension(self):
        from types import SimpleNamespace

        from telegram_vault.providers import TelethonProvider

        provider = object.__new__(TelethonProvider)
        for video, photo, ext, expected in [
            (True, None, ".mp4", "Video.mp4"),
            (False, SimpleNamespace(id=2), ".jpg", "Photo.jpg"),
            (False, None, ".pdf", "Document.pdf"),
        ]:
            raw = SimpleNamespace(
                id=10,
                date=datetime.now(ZoneInfo("UTC")),
                file=SimpleNamespace(name=None, ext=ext, mime_type="", size=10),
                document=SimpleNamespace(id=1),
                photo=photo,
                video=video,
                message="",
                reply_to=None,
            )
            self.assertEqual(provider.metadata(raw, 1, False).filename, expected)
        raw.file.name = "ActualName.mp4"
        self.assertEqual(provider.metadata(raw, 1, False).filename, "ActualName.mp4")

    async def test_album_sorted_id_and_caption_shared(self):
        from types import SimpleNamespace
        from unittest.mock import AsyncMock

        from scripts.audit_simulations import sandbox
        from telegram_vault.providers import TelethonProvider

        async with sandbox() as c:
            p = TelethonProvider(c.config, c.engine.rate)
            p.status = "connected"
            date = datetime(2025, 10, 4, tzinfo=ZoneInfo("UTC"))

            def member(mid, caption):
                return SimpleNamespace(
                    id=mid,
                    grouped_id=123456789,
                    message=caption,
                    date=date,
                    file=SimpleNamespace(name="test.mp4", mime_type="video/mp4", size=10),
                    document=SimpleNamespace(id=mid),
                    video=True,
                )

            first, second = member(4821, "Caption"), member(4822, "")
            p.client = SimpleNamespace(
                get_input_entity=AsyncMock(return_value="peer"),
                get_messages=AsyncMock(return_value=[second, first]),
            )
            result = await p.named_metadata(second, 1, False)
            self.assertEqual(
                (result.album_id, result.album_index, result.caption), (4821, 2, "Caption")
            )
            await p.named_metadata(first, 1, False)
            p.client.get_messages.assert_awaited_once()
