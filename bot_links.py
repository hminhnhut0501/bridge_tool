import os


def bot_username():
    return str(os.getenv("BOT_USERNAME", "") or "").strip().lstrip("@")


def bot_base_url():
    username = bot_username()
    if username:
        return f"https://t.me/{username}"
    return "https://t.me/"


def normalize_bot_link_template(value, *, default_payload="act_{code}"):
    template = str(value or "").strip()
    if not template:
        return f"{bot_base_url()}?start={default_payload}"
    if template.startswith("t.me/"):
        template = f"https://{template}"
    if template.startswith("https://t.me/") and "?" not in template:
        template = f"{template}?start={default_payload}"
    if "start=act_{code}" in template or "start={code}" in template:
        template = template.replace("start={code}", "start=act_{code}")
    return template

