# Architecture

Single Python process owns SQLite and the account session. FastAPI lifespan
starts scanner, transfer workers and maintenance; shutdown cancels and reaps
subprocesses, checkpoints WAL and closes the DB. A filesystem advisory lock
prevents two running engines claiming/reconciling the same database.

TelegramProvider isolates Telethon; MockTelegramProvider is selected explicitly
for local testing. AccountRateController serializes API operations, paces reads,
and persists an epoch FloodWait deadline. Library internal retries are disabled.
FloodWait pauses the account and reduces pressure without consuming job retry
budget. Never rotates account, IP or proxy.

History captures an upper message boundary and scans oldest-first in bounded
batches. Every message metadata insertion and checkpoint advance is one SQLite
transaction. Live delivery never advances the history checkpoint. Periodic
incremental catch-up captures all missed IDs, then recent messages catch edits.
A live video has priority 100, retry 50, historical 10; round-robin source order
within priority prevents a huge group permanently starving another.

Sources are soft-deleted. Completed remote objects are kept if messages/topics/
sources disappear. Stable chat/topic/message/media IDs are separate from names.
Each path is stored once; renaming a group/topic updates display only. Media
revision ID generates another logical record/path, never overwrites an old backup.

Worker: QUEUED/RETRY_WAIT → TRANSFERRING → VERIFYING → COMPLETED. A unique
`.incomplete/job-id/uuid` destination accepts `rcat --size` input. The plaintext
SHA-256 is persisted before verification/promotion. Recovery checks final and
known incomplete objects with saved digest; missing/uncertain data retries from
zero. Existing remote data without a matching persisted digest fails for review.
Full hash mode verifies before and after promotion, preventing a raced final
object of equal size being silently accepted. This rereads the payload twice.
Size-only mode is explicit in Settings; recovery of existing data always hashes.

RAM: 512 KiB reader chunk, asyncio pipe backpressure, 1 MiB rclone buffer,
8 MiB Drive chunks plus runtime/Telegram buffers. Application never uses a
full-file temporary plaintext file. Local test backend does store ciphertext.
Global Telegram download limiter is shared; upload cap is conservatively divided
among configured workers (current child processes keep their starting cap).

SQLite stats triggers update counts/bytes on state changes, so global dashboard
counts do not repeatedly scan media. Jobs/events/sources use bounded cursor pages.
There is no Redis, RC server or independent frontend development server in production.
