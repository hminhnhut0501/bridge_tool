import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

from modules import mod_engine, mod_general


def test_rendered_page_falls_back_to_text_when_menu_image_is_invalid(monkeypatch):
    sender = SimpleNamespace(answer_photo=AsyncMock(side_effect=mod_engine.TelegramBadRequest(method=None, message="bad photo")), answer=AsyncMock())
    monkeypatch.setattr(mod_engine, "send_with_html_fallback", AsyncMock(side_effect=[
        mod_engine.TelegramBadRequest(method=None, message="bad photo"),
        None,
    ]))

    asyncio.run(mod_engine.send_rendered_page(sender, img_url="https://invalid.example/image.jpg", text="Menu", reply_markup=None))

    assert mod_engine.send_with_html_fallback.await_count == 2
    assert "photo" not in mod_engine.send_with_html_fallback.await_args_list[1].kwargs


def test_rendered_page_falls_back_without_keyboard_when_button_data_invalid(monkeypatch):
    sender = SimpleNamespace(answer=AsyncMock())
    monkeypatch.setattr(mod_engine, "send_with_html_fallback", AsyncMock(side_effect=[
        mod_engine.TelegramBadRequest(method=None, message="BUTTON_DATA_INVALID"),
        None,
    ]))

    asyncio.run(mod_engine.send_rendered_page(sender, img_url="", text="Menu", reply_markup=object()))

    assert mod_engine.send_with_html_fallback.await_count == 2
    assert mod_engine.send_with_html_fallback.await_args_list[0].kwargs["reply_markup"] is not None
    assert mod_engine.send_with_html_fallback.await_args_list[1].kwargs["reply_markup"] is None


def test_menu_builder_skips_invalid_callback_data():
    long_action = "x" * 65

    markup = mod_engine.build_dynamic_keyboard(f"Too long => {long_action}\nOK => back_main")

    buttons = markup.inline_keyboard
    assert len(buttons) == 1
    assert buttons[0][0].callback_data == "back_main"


def test_change_language_sends_fallback_when_menu_render_fails(monkeypatch):
    callback = SimpleNamespace(
        data="set_lang:en",
        from_user=SimpleNamespace(id=123),
        answer=AsyncMock(),
        message=SimpleNamespace(answer=AsyncMock()),
    )
    monkeypatch.setattr(mod_general, "check_protection", AsyncMock(return_value=True))
    monkeypatch.setattr(mod_general, "set_user_language", lambda user_id, language: language)
    monkeypatch.setattr(mod_general, "render_page", AsyncMock(side_effect=RuntimeError("broken English page")))

    asyncio.run(mod_general.change_language(callback))

    callback.message.answer.assert_awaited_once()
    assert "/start" in callback.message.answer.await_args.args[0]
