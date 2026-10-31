# Troubleshooting

- Login required: stop service, set private API credentials, run CLI login, restart.
- Local password unknown: read data/local-access.txt from the local setup or run
  init-admin. AUTH_PASSWORD_HASH overrides a DB-stored hash if configured.
- CSRF/origin rejected: APP_URL must exactly match browser origin (scheme, host,
  port). Use 127.0.0.1 consistently rather than mixing localhost, or change APP_URL.
- Login is unavailable on remote HTTP: configure HTTPS and COOKIE_SECURE=true.
- Invalid crypt config: file exists, permissions 600, named remote type crypt,
  standard filename encryption and encrypted directories. Session/config owner
  must match service user. Config password encryption is unsupported.
- Google token refresh fails: mount private rclone config read-write, owned by UID
  10001 in Docker. Never return its contents through API or logs.
- FloodWait: wait until the persisted deadline; restart does not bypass the wait.
- Queued jobs do not move: verify account/storage connection, source pause/enabled,
  selected topics, size/date filters and account/storage retry deadlines.
- Remote conflict: inspect exact object and DB digest; do not blindly overwrite.
- Incomplete objects: retained on purpose. Review job/transfer history and clean only
  exact known failed TEST objects; never run a recursive deletion of backup root.
- Port in use: choose another port and matching APP_URL. This machine's ready UI
  uses 8787 because another application occupies 8080.
- Duplicate service: one process owns DB. Stop previous service; do not use uvicorn
  multiple workers or a production reload watcher.
- Blank UI: `cd frontend && npm ci && npm run build`, then serve backend. Production
  uses built assets; Vite development proxy needs matching APP_URL/port.
