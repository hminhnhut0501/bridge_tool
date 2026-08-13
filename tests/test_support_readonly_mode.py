import unittest
from types import SimpleNamespace

import support_utils


class FakeDb:
    def __init__(self, config):
        self.config = config

    def get_config(self, key, default=""):
        return self.config.get(key, default)


class FakeBot:
    def __init__(self):
        self.calls = []

    async def restrict_chat_member(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(ok=True)

    async def set_chat_permissions(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(ok=True)


class FakeChatPermissions:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class SupportReadonlyModeTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.original_db = support_utils.db
        self.original_bot = support_utils.bot
        self.original_chat_permissions = support_utils.ChatPermissions
        support_utils.ChatPermissions = FakeChatPermissions

    def tearDown(self):
        support_utils.db = self.original_db
        support_utils.bot = self.original_bot
        support_utils.ChatPermissions = self.original_chat_permissions

    async def test_view_only_mode_blocks_all_member_permissions(self):
        support_utils.db = FakeDb({"SUPPORT_GROUP_VIEW_ONLY_ENABLED": "ON"})
        fake_bot = FakeBot()
        support_utils.bot = fake_bot

        await support_utils.unmute_member("-100123", "42")

        self.assertEqual(len(fake_bot.calls), 1)
        permissions = fake_bot.calls[0]["permissions"]
        self.assertFalse(permissions.can_send_messages)
        self.assertFalse(permissions.can_send_audios)
        self.assertFalse(permissions.can_send_documents)
        self.assertFalse(permissions.can_send_photos)
        self.assertFalse(permissions.can_send_videos)
        self.assertFalse(permissions.can_send_video_notes)
        self.assertFalse(permissions.can_send_voice_notes)
        self.assertFalse(permissions.can_send_polls)
        self.assertFalse(permissions.can_send_other_messages)
        self.assertFalse(permissions.can_add_web_page_previews)

    async def test_non_view_only_mode_restores_member_send_rights(self):
        support_utils.db = FakeDb({"SUPPORT_GROUP_VIEW_ONLY_ENABLED": "OFF"})
        fake_bot = FakeBot()
        support_utils.bot = fake_bot

        await support_utils.unmute_member("-100123", "42")

        self.assertEqual(len(fake_bot.calls), 1)
        permissions = fake_bot.calls[0]["permissions"]
        self.assertTrue(permissions.can_send_messages)
        self.assertTrue(permissions.can_send_audios)
        self.assertTrue(permissions.can_send_documents)
        self.assertTrue(permissions.can_send_photos)
        self.assertTrue(permissions.can_send_videos)
        self.assertTrue(permissions.can_send_video_notes)
        self.assertTrue(permissions.can_send_voice_notes)
        self.assertTrue(permissions.can_send_polls)
        self.assertTrue(permissions.can_send_other_messages)
        self.assertTrue(permissions.can_add_web_page_previews)

    async def test_bulk_lock_sets_group_read_only_permissions(self):
        support_utils.db = FakeDb({"SUPPORT_GROUP_ID": "-1001234567890"})
        fake_bot = FakeBot()
        support_utils.bot = fake_bot

        locked_chat_id = await support_utils.lock_support_group_read_only()

        self.assertEqual(locked_chat_id, "-1001234567890")
        self.assertEqual(len(fake_bot.calls), 1)
        permissions = fake_bot.calls[0]["permissions"]
        self.assertFalse(permissions.can_send_messages)
        self.assertFalse(permissions.can_send_audios)
        self.assertFalse(permissions.can_send_documents)
        self.assertFalse(permissions.can_send_photos)
        self.assertFalse(permissions.can_send_videos)
        self.assertFalse(permissions.can_send_video_notes)
        self.assertFalse(permissions.can_send_voice_notes)
        self.assertFalse(permissions.can_send_polls)
        self.assertFalse(permissions.can_send_other_messages)
        self.assertFalse(permissions.can_add_web_page_previews)

    async def test_bulk_unlock_restores_group_read_write_permissions(self):
        support_utils.db = FakeDb({"SUPPORT_GROUP_ID": "-1001234567890"})
        fake_bot = FakeBot()
        support_utils.bot = fake_bot

        unlocked_chat_id = await support_utils.unlock_support_group_read_write()

        self.assertEqual(unlocked_chat_id, "-1001234567890")
        self.assertEqual(len(fake_bot.calls), 1)
        permissions = fake_bot.calls[0]["permissions"]
        self.assertTrue(permissions.can_send_messages)
        self.assertTrue(permissions.can_send_audios)
        self.assertTrue(permissions.can_send_documents)
        self.assertTrue(permissions.can_send_photos)
        self.assertTrue(permissions.can_send_videos)
        self.assertTrue(permissions.can_send_video_notes)
        self.assertTrue(permissions.can_send_voice_notes)
        self.assertTrue(permissions.can_send_polls)
        self.assertTrue(permissions.can_send_other_messages)
        self.assertTrue(permissions.can_add_web_page_previews)


if __name__ == "__main__":
    unittest.main()
