import os
from urllib.parse import urlparse


def bot_username():
    return str(os.getenv("BOT_USERNAME", "") or "").strip().lstrip("@")


def bot_version():
    return str(os.getenv("BOT_VERSION", "new") or "new").strip().lower()


def is_legacy_bot():
    return bot_version() in {"legacy", "old", "backup", "redirect"}


def bot_new_url():
    return str(os.getenv("BOT_NEW_URL", "") or "").strip()


def bot_base_url():
    new_url = bot_new_url()
    if new_url:
        return new_url
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
    if template.startswith("https://t.me/"):
        parsed = urlparse(template)
        path_parts = [part for part in parsed.path.split("/") if part]
        if path_parts:
            username = path_parts[0].lstrip("@").lower()
            legacy_usernames = {"hangcuprivebot", "your_bot_username"}
            if username in legacy_usernames:
                remainder = "/".join(path_parts[1:])
                template = bot_base_url()
                if remainder:
                    template = f"{template}/{remainder}"
                if parsed.query:
                    template = f"{template}?{parsed.query}"
        if "?" not in template:
            template = f"{template}?start={default_payload}"
    if "start={code}" in template:
        template = template.replace("start={code}", f"start={default_payload}")
    return template
