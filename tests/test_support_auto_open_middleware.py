import asyncio
import sys
import types
from types import SimpleNamespace
from unittest.mock import AsyncMock

_ORIGINAL_MODULES = dict(sys.modules)


def _install_stubs():
    aiogram_mod = types.ModuleType("aiogram")
    aiogram_mod.BaseMiddleware = object
    sys.modules["aiogram"] = aiogram_mod

    aiogram_types_mod = types.ModuleType("aiogram.types")
    aiogram_types_mod.Message = object
    aiogram_types_mod.CallbackQuery = object
    aiogram_types_mod.InputMediaPhoto = object
    sys.modules["aiogram.types"] = aiogram_types_mod

    aiogram_exceptions_mod = types.ModuleType("aiogram.exceptions")
    class TelegramBadRequest(Exception):
        pass
    aiogram_exceptions_mod.TelegramBadRequest = TelegramBadRequest
    sys.modules["aiogram.exceptions"] = aiogram_exceptions_mod

    database_mod = types.ModuleType("database")

    class FakeDB:
        def get_config(self, key, default=""):
            values = {
                "MAINTENANCE_MODE": "ON",
                "BOT_SCHEDULE_ENABLED": "OFF",
                "BOT_TIMEZONE": "Asia/Ho_Chi_Minh",
            }
            return values.get(key, default)

    database_mod.db = FakeDB()
    database_mod.normalize_key = lambda value: str(value or "").strip().upper()
    sys.modules["database"] = database_mod

    bot_instance_mod = types.ModuleType("bot_instance")
    bot_instance_mod.bot = SimpleNamespace()
    bot_instance_mod.is_spamming = lambda user_id: False
    sys.modules["bot_instance"] = bot_instance_mod

    i18n_mod = types.ModuleType("i18n")
    i18n_mod.t = lambda *args, **kwargs: kwargs.get("default", "") if "default" in kwargs else (args[2] if len(args) > 2 else "")
    sys.modules["i18n"] = i18n_mod

    supabase_store_mod = types.ModuleType("supabase_store")

    class FakeStore:
        enabled = True

        def get_open_support_ticket_by_user(self, user_id):
            return None

    supabase_store_mod.supabase_store = FakeStore()
    sys.modules["supabase_store"] = supabase_store_mod

    support_utils_mod = types.ModuleType("support_utils")
    support_utils_mod.create_support_case_from_private_message = AsyncMock(return_value=({"ticket_no": "SUP001"}, ""))
    sys.modules["support_utils"] = support_utils_mod


helpers = None


def setUpModule():
    global helpers
    _install_stubs()
    import helpers as imported_helpers

    helpers = imported_helpers


def tearDownModule():
    for name in list(sys.modules):
        if name not in _ORIGINAL_MODULES:
            sys.modules.pop(name, None)
    for name, module in _ORIGINAL_MODULES.items():
        sys.modules[name] = module


def test_middleware_auto_opens_support_case_when_bot_is_down():
    middleware = helpers.BotAvailabilityMiddleware()
    class FakeMessage(SimpleNamespace):
        pass

    event = FakeMessage(
        from_user=SimpleNamespace(id=123, is_bot=False),
        chat=SimpleNamespace(type="private"),
        text="hello",
        caption="",
        photo=None,
        document=None,
        video=None,
        voice=None,
        audio=None,
        sticker=None,
        answer=AsyncMock(),
    )
    handler = AsyncMock(return_value="handled")

    helpers.bot_unavailable_reason = lambda now=None: "maintenance"
    helpers.is_admin_user = lambda user_id: False
    helpers.has_open_support_ticket = lambda user_id: False
    helpers.is_private_user_content_message = lambda event: True
    helpers.is_private_interaction = lambda event: True
    helpers.check_protection = AsyncMock(return_value=True)
    helpers.Message = FakeMessage
    support_utils_mod = sys.modules["support_utils"]
    support_utils_mod.create_support_case_from_private_message = AsyncMock(
        return_value=({"ticket_no": "SUP001"}, "")
    )

    result = asyncio.run(middleware(handler, event, {}))

    assert result is None
    handler.assert_not_awaited()
    support_utils_mod.create_support_case_from_private_message.assert_awaited_once()
