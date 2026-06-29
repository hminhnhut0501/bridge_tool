import asyncio
import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock


def _install_stubs():
    class FakeRouter:
        def message(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

        def callback_query(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    class FakeFilter:
        def __getattr__(self, _name):
            return self

        def __call__(self, *args, **kwargs):
            return self

        def __eq__(self, other):
            return self

        def __or__(self, other):
            return self

        def in_(self, *_args, **_kwargs):
            return self

        def startswith(self, *_args, **_kwargs):
            return self

    class FakeCommand:
        def __init__(self, *args, **kwargs):
            pass

    class FakeCommandStart(FakeCommand):
        pass

    class FakeInlineKeyboardButton:
        def __init__(self, *args, **kwargs):
            self.text = kwargs.get("text")
            self.callback_data = kwargs.get("callback_data")

    class FakeInlineKeyboardBuilder:
        def row(self, *args, **kwargs):
            return self

        def as_markup(self):
            return None

    database_mod = types.ModuleType("database")

    class FakeDB:
        def __init__(self):
            self.config = {
                "MAINTENANCE_MODE": "ON",
                "BOT_SCHEDULE_ENABLED": "OFF",
                "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
            }

        def get_config(self, key, default=""):
            return self.config.get(key, default)

        def reload_config(self, force=False):
            return None

    database_mod.db = FakeDB()
    sys.modules["database"] = database_mod

    bot_instance_mod = types.ModuleType("bot_instance")
    bot_instance_mod.bot = SimpleNamespace()
    bot_instance_mod.is_spamming = lambda user_id: False
    sys.modules["bot_instance"] = bot_instance_mod

    aiogram_mod = types.ModuleType("aiogram")
    aiogram_mod.Router = FakeRouter
    aiogram_mod.F = FakeFilter()
    aiogram_mod.BaseMiddleware = object
    sys.modules["aiogram"] = aiogram_mod

    aiogram_types_mod = types.ModuleType("aiogram.types")
    aiogram_types_mod.Message = object
    aiogram_types_mod.CallbackQuery = object
    aiogram_types_mod.InlineKeyboardButton = FakeInlineKeyboardButton
    aiogram_types_mod.InputMediaPhoto = object
    sys.modules["aiogram.types"] = aiogram_types_mod

    aiogram_exceptions_mod = types.ModuleType("aiogram.exceptions")
    class TelegramBadRequest(Exception):
        pass
    aiogram_exceptions_mod.TelegramBadRequest = TelegramBadRequest
    sys.modules["aiogram.exceptions"] = aiogram_exceptions_mod

    aiogram_filters_mod = types.ModuleType("aiogram.filters")
    aiogram_filters_mod.Command = FakeCommand
    aiogram_filters_mod.CommandStart = FakeCommandStart
    sys.modules["aiogram.filters"] = aiogram_filters_mod

    aiogram_utils_keyboard_mod = types.ModuleType("aiogram.utils.keyboard")
    aiogram_utils_keyboard_mod.InlineKeyboardBuilder = FakeInlineKeyboardBuilder
    sys.modules["aiogram.utils.keyboard"] = aiogram_utils_keyboard_mod

    modules_engine_mod = types.ModuleType("modules.mod_engine")
    modules_engine_mod.build_dynamic_keyboard = lambda *args, **kwargs: None
    modules_engine_mod.page_exists = lambda *args, **kwargs: False
    modules_engine_mod.render_page = AsyncMock(return_value=False)
    modules_engine_mod.send_with_html_fallback = AsyncMock(return_value=None)
    sys.modules["modules.mod_engine"] = modules_engine_mod

    scheduler_mod = types.ModuleType("scheduler")
    scheduler_mod.check_expirations_professional = AsyncMock(return_value=None)
    sys.modules["scheduler"] = scheduler_mod

    renewal_utils_mod = types.ModuleType("renewal_utils")
    renewal_utils_mod.is_early_renew_enabled = lambda: False
    sys.modules["renewal_utils"] = renewal_utils_mod

    sale_utils_mod = types.ModuleType("sale_utils")
    sale_utils_mod.build_sale_announcement = AsyncMock(return_value=False)
    sys.modules["sale_utils"] = sale_utils_mod

    support_utils_mod = types.ModuleType("support_utils")
    support_utils_mod.create_support_invite_link = AsyncMock(return_value=("", ""))
    sys.modules["support_utils"] = support_utils_mod

    i18n_mod = types.ModuleType("i18n")
    i18n_mod.get_user_language = lambda user_id: "vi"
    i18n_mod.set_user_language = lambda user_id, language: language
    i18n_mod.t = lambda *args, **kwargs: kwargs.get("default", "") if "default" in kwargs else (args[2] if len(args) > 2 else "")
    sys.modules["i18n"] = i18n_mod


_install_stubs()

from modules import mod_general  # noqa: E402


def test_start_activation_payload_bypasses_maintenance_gate():
    message = SimpleNamespace(
        text="/start act_manual_123",
        from_user=SimpleNamespace(id=789, username="user789", full_name="User 789"),
        chat=SimpleNamespace(id=789),
        entities=[],
        answer=AsyncMock(),
    )

    mod_general.db.reload_config = lambda force=False: None
    mod_general.cleanup_welcome = AsyncMock()
    mod_general.record_start_event = AsyncMock()
    mod_general.deliver_activation_order = AsyncMock()
    mod_general.check_protection = AsyncMock(return_value=True)
    mod_general.send_sale_announcement = AsyncMock(return_value=False)
    mod_general.render_page = AsyncMock(return_value=False)
    mod_general.bot_unavailable_reason = lambda now=None: "maintenance"
    mod_general.is_admin_user = lambda user_id: False

    asyncio.run(mod_general.cmd_start(message))

    mod_general.deliver_activation_order.assert_awaited_once_with(message, "manual_123")
    message.answer.assert_not_awaited()
