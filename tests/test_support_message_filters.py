from message_filter_utils import is_private_non_command_message


def test_private_non_command_filter_ignores_commands():
    assert not is_private_non_command_message("private", "/start")
    assert not is_private_non_command_message("private", "/support")


def test_private_non_command_filter_accepts_plain_text():
    assert is_private_non_command_message("private", "Xin chào admin")


def test_private_non_command_filter_does_not_touch_non_private_chats():
    assert not is_private_non_command_message("group", "Xin chào admin")
    assert not is_private_non_command_message("supergroup", "Xin chào admin")

