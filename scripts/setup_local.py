"""Prepare an isolated local mock + real crypt service. Never touches user remotes."""

import os
import secrets
import subprocess
from pathlib import Path

from argon2 import PasswordHasher

from telegram_vault.config import Config
from telegram_vault.database import Database

os.umask(0o077)
root = Path(__file__).resolve().parent.parent
os.chdir(root)
config = root / "data/local-crypt/rclone.conf"
if not config.exists():
    subprocess.run([str(root / ".venv/bin/python"), "scripts/local_crypt.py"], check=True)
env = root / ".env"
if env.exists():
    raise SystemExit(".env already exists; not overwriting existing setup")
password = secrets.token_urlsafe(18)
db = Database(Config().database_path)
db.set_setting("admin_password_hash", PasswordHasher().hash(password))
db.close()
env.write_text(
    f"TELEGRAM_MODE=mock\nRCLONE_CONFIG={config}\nRCLONE_REMOTE=crypt:\nSTORAGE_ROOT=TelegramVault_TEST\nAPP_URL=http://127.0.0.1:8080\nAPP_PORT=8080\nCOOKIE_SECURE=false\n"
)
access = root / "data/local-access.txt"
access.write_text(
    f"Local test UI: http://127.0.0.1:8080\nUsername: admin\nPassword: {password}\n\nUse telegram-vault init-admin to change this password.\n"
)
print("Local setup ready. Credentials saved privately in data/local-access.txt")
