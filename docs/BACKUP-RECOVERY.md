# Backup and recovery

Maintenance takes a transaction-consistent SQLite online backup once per day and
retains 14 auto snapshots in DATA_DIR/db-backups. `telegram-vault backup-db`
creates an additional manual snapshot. Snapshots include hashes, checkpoints,
queue, source configuration and web auth hashes/sessions; keep permissions private.
No session or rclone config is uploaded to cloud by default.

## New VPS

1. Install code/dependencies or build the image. Stop service during restore.
2. Copy one verified SQLite snapshot to DATABASE_PATH. Do not copy a live DB file
   without WAL; use the backup command or a clean shutdown.
3. Privately restore rclone config and encryption keys. Preserve original remote
   and STORAGE_ROOT; paths in the DB must address the same storage.
4. Provision the account session separately, or re-login with CLI on the new VPS.
5. Restrict data/session directories 700 and config/DB files 600; match service UID.
6. Start service. Interrupted TRANSFERRING/VERIFYING jobs become recoverable retry
   jobs; saved cancellation intent is applied. Existing remote targets are hashed
   before being reconciled as completed. Incomplete/uncertain objects stay incomplete.
7. Run read-only doctor and Storage → Reconcile; inspect missing/conflict events.
8. Reset admin password with init-admin to revoke restored web sessions. Enable
   HTTPS and service autostart, test one TEST video and a reboot before production.

## Failure at 99%

Before successful verify, completion remains false. Stream cannot resume at byte
99%; retry starts from zero unless a complete known temporary/final object can
be validated by saved digest. Retries back off; permanent deleted/replaced media
or remote conflicts go to FAILED for review. Backups are never deleted when the
original Telegram message disappears.

Use service graceful shutdown for routine updates. Hard-kill process-group tests
at 10/50/90% pass locally. A VPS reboot test on Linux remains an acceptance item.
