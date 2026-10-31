# Telegram setup and behavior

## Web sign-in

Sign in to the administrator UI and open **Kết nối Telegram**. Provide API ID/API hash from [Telegram API development tools](https://my.telegram.org/apps), then phone in international format, OTP, and Telegram 2FA password if requested. See [official API setup](https://core.telegram.org/api/obtaining_api_id) and [Telethon auth](https://docs.telethon.dev/en/stable/modules/client.html#telethon.client.auth.AuthMethods.sign_in).

Web endpoints are administrator-only, with CSRF/origin checks. OTP and 2FA are processed in memory and never stored in DB/config. API ID/hash are stored atomically in a private 600 `DATA_DIR/telegram-api.json`, which overrides environment API values on restart. API hash, full phone, code hash and session bytes are never returned by REST; pending challenge state is scoped to the web session that began it. Config and Telegram session files must be backed up privately.

At least 60 seconds between send attempts; at most 5 verification submissions per challenge, then 60-second pause. FloodWait uses the existing persisted account-wide rate controller. A challenge expires after 10 minutes and is lost on server restart: request a fresh code. A completed Telegram session survives restart. Maintenance reconnect uses the same operation lock as web auth. Account binding prevents a restored different account from activating existing sources.

Ngắt kết nối signs out and removes the Telegram session; pause all sources and wait for active transfers first. Backups are retained. To switch accounts, remove old sources before connecting the different account.

CLI remains an alternative: stop the service before `telegram-vault login` to avoid sharing a session concurrently. Phone/OTP/2FA prompts then stay in that terminal. Session path: TELEGRAM_SESSION_PATH, default `data/session/account.session`, directory 700, process umask 077. On the VPS, use the service user and env file documented in the deployment report.

Discovery returns account-accessible groups/supergroups. Forum discovery uses
raw messages.GetForumTopicsRequest pagination; General is topic 1, normal groups
use topic 0. Topic root comes from reply_to_top_id, or the forum root reply ID.
Topics not yet known get stable ID-based placeholders; discovery can refresh names.

NewMessage and MessageEdited events enqueue only configured sources. Delete
updates are ignored. History checkpoint is independent of live events so a
reconnect gap cannot be skipped. FloodWait timestamp is persisted in settings.
During that interval scanner/transfer/discovery makes no further API attempts.
The live callback stores metadata only and does not download inside the handler.

See TELEGRAM-ARCHITECTURE.md for library decision and primary references. Actual
account/topic behavior and large file availability require an account-backed test.
