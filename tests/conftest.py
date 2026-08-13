from pathlib import Path
import sys
import types


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _install_aiogram_stub():
    if "aiogram" in sys.modules:
        return

    aiogram_mod = types.ModuleType("aiogram")

    class _Router:
        def __init__(self, *args, **kwargs):
            pass

    class _F:
        def __getattr__(self, name):
            return self

        def __call__(self, *args, **kwargs):
            return self

    aiogram_mod.Router = _Router
    aiogram_mod.F = _F()
    sys.modules["aiogram"] = aiogram_mod

    exceptions_mod = types.ModuleType("aiogram.exceptions")
    class _TelegramError(Exception):
        pass
    exceptions_mod.TelegramBadRequest = _TelegramError
    exceptions_mod.TelegramForbiddenError = _TelegramError
    sys.modules["aiogram.exceptions"] = exceptions_mod

    types_mod = types.ModuleType("aiogram.types")
    for name in ["InlineKeyboardButton", "ChatPermissions", "CallbackQuery", "Message", "ChatMemberUpdated", "BotCommand"]:
        setattr(types_mod, name, type(name, (), {}))
    sys.modules["aiogram.types"] = types_mod

    utils_mod = types.ModuleType("aiogram.utils")
    sys.modules["aiogram.utils"] = utils_mod

    keyboard_mod = types.ModuleType("aiogram.utils.keyboard")

    class InlineKeyboardBuilder:
        def row(self, *args, **kwargs):
            return self

        def as_markup(self):
            return None

    keyboard_mod.InlineKeyboardBuilder = InlineKeyboardBuilder
    sys.modules["aiogram.utils.keyboard"] = keyboard_mod

    filters_mod = types.ModuleType("aiogram.filters")
    filters_mod.Command = object
    sys.modules["aiogram.filters"] = filters_mod

    dispatcher_bases_mod = types.ModuleType("aiogram.dispatcher.event.bases")
    dispatcher_bases_mod.SkipHandler = type("SkipHandler", (Exception,), {})
    sys.modules["aiogram.dispatcher.event.bases"] = dispatcher_bases_mod


_install_aiogram_stub()
