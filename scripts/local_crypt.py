"""Create isolated local encrypted test storage; never modifies user remotes."""

import os
import secrets
import subprocess
from pathlib import Path

os.umask(0o077)
root = Path("data/local-crypt").resolve()
root.mkdir(parents=True, exist_ok=True, mode=0o700)
config = root / "rclone.conf"
if config.exists():
    raise SystemExit("Config already exists; reuse it instead of replacing encryption keys")


def obscure():
    return (
        subprocess.check_output(
            ["rclone", "obscure", "-"], input=secrets.token_bytes(32).hex().encode()
        )
        .decode()
        .strip()
    )


config.write_text(
    f"[crypt]\ntype = crypt\nremote = {root / 'encrypted'}\nfilename_encryption = standard\ndirectory_name_encryption = true\npassword = {obscure()}\npassword2 = {obscure()}\n"
)
config.chmod(0o600)
print(f"Local TEST config created: {config}")
