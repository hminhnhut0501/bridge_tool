def is_private_non_command_message(chat_type, text):
    return str(chat_type or "").strip() == "private" and not str(text or "").strip().startswith("/")
