# Local → Ubuntu VPS deployment

The current release is deployed on Ubuntu VPS; see [deployment evidence](VPS-DEPLOYMENT-2026-10-06.md). The running local
instance uses an explicitly labeled mock Telegram account with real local crypt.
Production acceptance still needs the real account, Google Drive and Linux.

## Source upload

Generate the source-only archive:

```sh
.venv/bin/python scripts/package_release.py
```

Upload `data/releases/telegram-vault-0.2.0.tar.gz` by SCP/SFTP to the chosen VPS,
then extract. The archive excludes `.env`, data, DB, Telegram sessions, rclone
configs, private directories, caches, node_modules and generated artifacts.
Install credentials separately. The source release was uploaded in the VPS deployment recorded above.

## Docker + Caddy

Prerequisites: Ubuntu VPS with Docker Engine + Compose plugin, 2 vCPU / 2 GB RAM,
DNS domain pointing to VPS, HTTPS ports 80/443 reachable. Audit OS/RAM/disk/network
and existing services/remotes read-only first. The backend host port is loopback.

```sh
cp .env.example .env.production
chmod 600 .env.production
mkdir -p private/rclone
# Privately install the configured rclone.conf here; never print it.
sudo chown -R 10001:10001 private/rclone
sudo chmod 700 private/rclone
sudo chmod 600 private/rclone/rclone.conf
# Edit .env.production: API credentials, HTTPS APP_URL, domain, secure cookies.
docker compose --env-file .env.production build
# CLI initialization before starting the service; prompts stay in terminal.
docker compose --env-file .env.production run --rm vault telegram-vault init-admin
docker compose --env-file .env.production run --rm vault telegram-vault login
docker compose --env-file .env.production --profile https up -d
```

Persistent named volume vault-data contains /data/db, /data/session, /data/cache
(only streaming currently uses the app). rclone config is a separate private
read-write bind mount so Drive OAuth token refresh can persist. Owner UID 10001
matches non-root container. Content/filename/directory encryption is required.
No RC port is exposed. Access the app at APP_URL; cookie Secure=true.

Health checks use /api/health locally without touching Telegram. Public health
returns only app+SQLite health; authenticated dashboard includes cached remote
and account status. Logs rotate at 10 MB × 3 in Compose. Restart unless-stopped
starts the service after reboot. Config errors remain visible in dashboard and
do not trigger rapid account login/restart loops.

Default container resource budget is 768 MB and 2 CPUs; benchmark on target
before tightening it. Default DOWNLOAD_CONCURRENCY=1; cap 2. Local one/two worker
benchmark is synthetic and not a reason to increase production Telegram pressure.

## Native systemd

Install Python packages with umask 022 so the service user can import them; use 077 for runtime secrets/data. Web Telegram sign-in is available after administrator setup; see [web login](TELEGRAM-WEB-LOGIN.md).

Create user telegram-vault, install source under /opt/telegram-vault and a venv.
Build frontend and set FRONTEND_DIR=/opt/telegram-vault/frontend/dist. Install
env at /etc/telegram-vault/vault.env (root:telegram-vault, 640) with:

```ini
DATA_DIR=/var/lib/telegram-vault
DATABASE_PATH=/var/lib/telegram-vault/db/vault.sqlite3
TELEGRAM_SESSION_PATH=/var/lib/telegram-vault/session/account
RCLONE_CONFIG=/var/lib/telegram-vault/rclone/rclone.conf
APP_URL=https://vault.example.com
COOKIE_SECURE=true
TELEGRAM_MODE=real
```

The private data rclone.conf must be owned by telegram-vault, mode 600, and its containing
directory permit atomic config writes for token refresh. Include private API
credentials and the chosen crypt remote/root in the env. Initialize private
data dirs, run init-admin/login as that user with the same environment, then
install deploy/telegram-vault.service and enable with systemctl. Native Caddy
uses deploy/Caddyfile.native; substitute the actual domain or configure its
VAULT_DOMAIN environment. systemd supports only /var/lib/telegram-vault writes;
the example keeps the writable OAuth config under that private data directory.

Journald handles native logging; configure its system retention limits. Routine
updates stop service gracefully, preserve data and backup DB before installation.
For locally built images, use docker compose build + up -d; pull + up -d applies
when you publish an image in your own registry. DB bootstrap migration takes a
snapshot before modifying an existing version-0 database; newer schemas fail
closed rather than being silently downgraded.

## Go-live checks

Start with TEST root and one source. Verify a real video, decrypted hash,
resource ceilings, FloodWait/retry and restart behavior. Test actual VPS reboot
and Drive 429 behavior. Then configure production root/DB deliberately. Neither
Docker runtime nor actual VPS reboot has been executed on this Mac (no daemon).
