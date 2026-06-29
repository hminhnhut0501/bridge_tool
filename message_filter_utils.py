def is_private_non_command_message(chat_type, text):
    return str(chat_type or "").strip() == "private" and not str(text or "").strip().startswith("/")


def is_private_user_content_message(message):
    if not message or str(getattr(message.chat, "type", "") or "").strip() != "private":
        return False
    from_user = getattr(message, "from_user", None)
    if not from_user or getattr(from_user, "is_bot", False):
        return False
    text = str(getattr(message, "text", "") or "").strip()
    if text.startswith("/"):
        return False
    return bool(
        text
        or str(getattr(message, "caption", "") or "").strip()
        or getattr(message, "photo", None)
        or getattr(message, "document", None)
        or getattr(message, "video", None)
        or getattr(message, "voice", None)
        or getattr(message, "audio", None)
        or getattr(message, "sticker", None)
    )
