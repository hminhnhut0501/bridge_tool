import os
import sys
import types
import unittest
from datetime import datetime, timedelta


def _install_stub_modules():
    class FakeDb:
        def __init__(self):
            self.config = {
                "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
                "SUPPORT_GROUP_ENABLED": "ON",
                "SUPPORT_GROUP_MUTE_ENABLED": "ON",
                "SUPPORT_GROUP_ID": "-100999",
                "SUPPORT_GROUP_NAME": "Nhóm hỗ trợ",
                "SUPPORT_GROUP_GRACE_DAYS": "14",
                "KICK_RECHECK_COOLDOWN_MINUTES": "1440",
                "BTN_G1": "Hang Cú Prime",
                "ID_G1": "-100111",
                "BTN_G2": "Hang Cú Boy",
                "ID_G2": "-100222",
            }

        def get_config(self, key, default=""):
            return self.config.get(key, default)

    class FakeStore:
        enabled = True

        def __init__(self):
            self.events = []

        def latest_support_event(self, event_type, telegram_user_id=None, order_id=None, chat_id=None):
            matches = [
                event for event in self.events
                if event["event_type"] == event_type
                and (telegram_user_id is None or str(event.get("telegram_user_id")) == str(telegram_user_id))
                and (order_id is None or str(event.get("order_id")) == str(order_id))
                and (chat_id is None or str(event.get("chat_id")) == str(chat_id))
            ]
            return matches[-1] if matches else None

        def record_support_event(self, event_type, telegram_user_id=None, **kwargs):
            self.events.append({
                "event_type": event_type,
                "telegram_user_id": str(telegram_user_id),
                "created_at": kwargs.pop("created_at", datetime(2026, 5, 25, 12, 0, 0).isoformat()),
                **kwargs,
            })

    class FakeBot:
        def __init__(self):
            self.kicked = []
            self.present = {}
            self.statuses = {}

        async def get_chat_member(self, chat_id, user_id):
            present = self.present.get((str(chat_id), str(user_id)), True)
            status = self.statuses.get((str(chat_id), str(user_id)), "member" if present else "left")

            class Member:
                pass

            Member.status = status
            Member.is_member = present
            return Member()

        async def ban_chat_member(self, chat_id, user_id):
            self.kicked.append((str(chat_id), str(user_id)))
            self.present[(str(chat_id), str(user_id))] = False

        async def unban_chat_member(self, chat_id, user_id):
            return None

    fake_db = FakeDb()
    fake_store = FakeStore()
    fake_bot = FakeBot()

    database_mod = types.ModuleType("database")
    database_mod.db = fake_db
    database_mod.normalize_key = lambda value: str(value or "").strip()
    sys.modules["database"] = database_mod

    bot_instance_mod = types.ModuleType("bot_instance")
    bot_instance_mod.bot = fake_bot
    sys.modules["bot_instance"] = bot_instance_mod

    aiogram_mod = types.ModuleType("aiogram")
    aiogram_mod.Router = object
    aiogram_mod.F = object
    sys.modules["aiogram"] = aiogram_mod

    aiogram_types_mod = types.ModuleType("aiogram.types")
    aiogram_types_mod.InlineKeyboardButton = object
    aiogram_types_mod.ChatPermissions = object
    aiogram_types_mod.CallbackQuery = object
    aiogram_types_mod.Message = object
    aiogram_types_mod.ChatMemberUpdated = object
    aiogram_types_mod.BotCommand = object
    sys.modules["aiogram.types"] = aiogram_types_mod

    aiogram_utils_mod = types.ModuleType("aiogram.utils")
    sys.modules["aiogram.utils"] = aiogram_utils_mod
    keyboard_mod = types.ModuleType("aiogram.utils.keyboard")

    class InlineKeyboardBuilder:
        def row(self, *args, **kwargs):
            return self

        def as_markup(self):
            return None

    keyboard_mod.InlineKeyboardBuilder = InlineKeyboardBuilder
    sys.modules["aiogram.utils.keyboard"] = keyboard_mod

    aiogram_filters_mod = types.ModuleType("aiogram.filters")
    aiogram_filters_mod.Command = object
    sys.modules["aiogram.filters"] = aiogram_filters_mod

    aiogram_fsm_context_mod = types.ModuleType("aiogram.fsm.context")
    aiogram_fsm_context_mod.FSMContext = object
    sys.modules["aiogram.fsm.context"] = aiogram_fsm_context_mod
    aiogram_fsm_state_mod = types.ModuleType("aiogram.fsm.state")
    aiogram_fsm_state_mod.State = object
    aiogram_fsm_state_mod.StatesGroup = object
    sys.modules["aiogram.fsm.state"] = aiogram_fsm_state_mod

    config_utils_mod = types.ModuleType("config_utils")
    config_utils_mod.config_int = lambda key, default, minimum=None, maximum=None: default
    config_utils_mod.group_numbers = lambda: range(1, 3)
    sys.modules["config_utils"] = config_utils_mod

    hidden_group_utils_mod = types.ModuleType("hidden_group_utils")
    hidden_group_utils_mod.is_lifetime_order = lambda plan_name: False
    def resolve_plan_groups(plan_name):
        plan = str(plan_name or "").lower()
        if "prime" in plan:
            return [("-100111", "Hang Cú Prime")]
        if "boy" in plan or "asia" in plan:
            return [("-100222", "Hang Cú Boy")]
        return [("-100111", "Hang Cú Prime")]

    hidden_group_utils_mod.resolve_plan_groups = resolve_plan_groups
    sys.modules["hidden_group_utils"] = hidden_group_utils_mod

    i18n_mod = types.ModuleType("i18n")
    i18n_mod.get_user_language = lambda user_id: "vi"
    sys.modules["i18n"] = i18n_mod

    renewal_utils_mod = types.ModuleType("renewal_utils")
    renewal_utils_mod.build_early_renew_block = lambda offer: ""
    renewal_utils_mod.build_early_renew_offer = lambda row, offer_ref, now, currency=None: None
    sys.modules["renewal_utils"] = renewal_utils_mod

    supabase_store_mod = types.ModuleType("supabase_store")
    supabase_store_mod.supabase_store = fake_store
    sys.modules["supabase_store"] = supabase_store_mod

    support_utils_mod = types.ModuleType("support_utils")
    support_utils_mod.is_lifetime_plan = lambda plan_name: "LIFE" in str(plan_name).upper()
    support_utils_mod.is_support_group = lambda chat_id: str(chat_id) == "-100999"
    support_utils_mod.mute_member = lambda chat_id, user_id: None
    support_utils_mod.unmute_member = lambda chat_id, user_id: None
    async def revoke_support_invite_link(chat_id, invite_link):
        return True, ""

    support_utils_mod.revoke_support_invite_link = revoke_support_invite_link
    support_utils_mod.record_support_event = fake_store.record_support_event
    support_utils_mod.support_group_enabled = lambda: True
    support_utils_mod.support_group_grace_days = lambda: 14
    support_utils_mod.support_group_id = lambda: "-100999"
    support_utils_mod.support_group_mute_enabled = lambda: True
    sys.modules["support_utils"] = support_utils_mod

    return fake_db, fake_store, fake_bot


os.environ.setdefault("BOT_TOKEN", "123456:TEST")
_FAKE_DB, _FAKE_STORE, _FAKE_BOT = _install_stub_modules()

import scheduler  # noqa: E402


class SchedulerHarnessTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        scheduler.db = _FAKE_DB
        scheduler.supabase_store = _FAKE_STORE
        scheduler.bot = _FAKE_BOT
        scheduler.recent_kicks.clear()
        _FAKE_STORE.events.clear()
        _FAKE_BOT.kicked.clear()
        _FAKE_BOT.present.clear()
        _FAKE_BOT.statuses.clear()

    async def test_finalized_kick_blocks_repeat_recheck(self):
        now = datetime(2026, 5, 25, 21, 20, 0)
        scheduler.now_local = lambda: now
        rows = [["old", "42", "User", "VIP 1 ngày - Hang Cú Asia", "0", "PAID", "", "2026-05-25 21:19:00"]]
        _FAKE_BOT.present[("-100222", "42")] = True
        _FAKE_STORE.events.append({
            "event_type": "member_kick_closed",
            "telegram_user_id": "42",
            "chat_id": "-100222",
            "order_id": "old",
            "plan_name": "VIP 1 ngày - Hang Cú Asia",
            "created_at": now.isoformat(),
        })

        expired_groups, errors = await scheduler.process_vip_kicks_for_expired_order(
            "42", "old", "VIP 1 ngày - Hang Cú Asia", "2026-05-25 21:19:00", rows, now
        )

        self.assertEqual(expired_groups, ["-100222"])
        self.assertEqual(errors, [])
        self.assertEqual(_FAKE_BOT.kicked, [])

    async def test_kick_finalization_is_written_once(self):
        now = datetime(2026, 5, 25, 21, 20, 0)
        scheduler.now_local = lambda: now
        _FAKE_BOT.present[("-100222", "42")] = True

        ok = await scheduler.ensure_member_kicked(
            "-100222",
            "42",
            "old",
            "VIP 1 ngày - Hang Cú Asia",
            "vip_expired",
            raw_data={"expire_at": "2026-05-25 21:19:00"},
        )

        self.assertTrue(ok)
        self.assertEqual(_FAKE_BOT.kicked, [("-100222", "42")])
        self.assertEqual([event["event_type"] for event in _FAKE_STORE.events], ["member_kicked", "member_kick_closed"])

if __name__ == "__main__":
    unittest.main()
