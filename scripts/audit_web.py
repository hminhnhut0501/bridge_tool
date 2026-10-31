"""Run browser E2E on a disposable account/DB/crypt server, not the user's instance."""

import asyncio
import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path

import httpx
from audit_simulations import PASSWORD, sandbox


async def run():
    async with sandbox() as c:
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        url = f"http://127.0.0.1:{port}"
        access = c.root / "access.txt"
        access.write_text(f"Username: admin\nPassword: {PASSWORD}\n")
        access.chmod(0o600)
        output = Path("data/reports/audit-web").resolve()
        output.mkdir(parents=True, exist_ok=True)
        env = {
            **os.environ,
            "DATA_DIR": str(c.root),
            "DATABASE_PATH": c.config.database_path,
            "TELEGRAM_MODE": "mock",
            "TELEGRAM_API_ID": "",
            "TELEGRAM_API_HASH": "",
            "TELEGRAM_SESSION_PATH": str(c.root / "session/account"),
            "RCLONE_CONFIG": str(c.root / "rclone.conf"),
            "RCLONE_REMOTE": "crypt:",
            "STORAGE_ROOT": "TelegramVault_TEST",
            "AUTH_PASSWORD_HASH": c.config.password_hash,
            "AUTH_USERNAME": "admin",
            "APP_URL": url,
            "COOKIE_SECURE": "false",
            "VAULT_E2E_URL": url,
            "VAULT_E2E_ACCESS": str(access),
            "VAULT_E2E_SCREENSHOTS": str(output),
        }
        with (c.root / "server.log").open("w") as log:
            server = subprocess.Popen(
                [".venv/bin/telegram-vault", "serve", "--port", str(port)],
                env=env,
                stdout=log,
                stderr=log,
                start_new_session=True,
            )
            try:
                async with httpx.AsyncClient() as client:
                    deadline = time.monotonic() + 15
                    while time.monotonic() < deadline:
                        if server.poll() is not None:
                            raise RuntimeError("Isolated test server stopped")
                        try:
                            if (await client.get(url + "/api/health")).status_code == 200:
                                break
                        except httpx.HTTPError:
                            pass
                        await asyncio.sleep(0.1)
                    else:
                        raise TimeoutError("Isolated server failed to start")
                browser = await asyncio.create_subprocess_exec(
                    "npm", "run", "test:e2e", cwd="frontend", env=env
                )
                code = await browser.wait()
                report = {
                    "verdict": "PASS" if code == 0 else "FAIL",
                    "exit_code": code,
                    "isolated_database": True,
                    "isolated_crypt_storage": True,
                    "production_instance_touched": False,
                    "screenshots": str(output),
                }
                (output / "result.json").write_text(json.dumps(report, indent=2))
                print(json.dumps(report, indent=2))
                if code:
                    raise RuntimeError("Browser E2E failed")
            finally:
                if server.poll() is None:
                    os.killpg(server.pid, signal.SIGTERM)
                    try:
                        await asyncio.to_thread(server.wait, 10)
                    except subprocess.TimeoutExpired:
                        os.killpg(server.pid, signal.SIGKILL)
                        await asyncio.to_thread(server.wait)


if __name__ == "__main__":
    asyncio.run(run())
