# Migration to gcrypt — 2026-10-07

Authorized scope: copy completed backups and direct future Telegram uploads to gcrypt, retaining the old remote. gcrypt wraps hangcu:Encrypted; gcrypt_kis wraps kis. Both use matching crypt keys and encrypted filenames/directories.

VPS migration runs under vault-migrate-gcrypt.service independently of the SSH connection. Private status, manifest, config/database backups and rclone logs live in /var/backups/telegram-vault/migrate-gcrypt-20261007 (restricted permissions). The script snapshots completed jobs after graceful worker stop, places a shared upload pause, then restores the web service while copying. It uses files-from-raw and immutable copy, never sync or delete against the old remote. Destination SHA-256 and logical size must match each completed job before switching the app config. Pending temp paths are reset when switching so old-remote incomplete uploads are not reused.

Initial manifest: 39 completed files, 7,333,502,648 bytes. Destination 1 MiB upload probe and cleanup succeeded after an initial transient DNS timeout. Server-side cross-config copy probe failed with Google 404; no sharing permissions were changed. Copy therefore streams through VPS with two transfers.

The app remains on the old remote until all destination verification passes. Failed migration is reported in status.json and does not silently claim success. Original backups remain for rollback. Never expose config files or raw remote filenames in public logs.

Completed: all 39 files (7,333,502,648 bytes) passed destination logical size and plaintext SHA-256 verification. Slow single-stream copy was replaced with encrypted disk staging and multistream downloads for remaining files. Verification used two parallel multistream encrypted downloads, followed by local crypt decryption streamed into the SHA-256 calculator; plaintext was never written to disk. Temporary encrypted files and verification config were removed after success. Application now uses gcrypt, shared storage cooldown cleared, user pause/cancel settings preserved. Config ownership for the service user is enforced at startup. Originals remain on gcrypt_kis.
