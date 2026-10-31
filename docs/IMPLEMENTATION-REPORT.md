# Implementation report — 2026-10-06

Follow-up adversarial testing reproduced seven weaknesses, including four P1
issues to fix before unattended VPS operation. See [simulation audit](SIMULATION-AUDIT.md).
All four P1 issues were subsequently fixed and passed regression tests; see [remediation](P1-REMEDIATION.md). Three P2 issues and live integration acceptance remain pending.

Implemented **standalone streaming core + authenticated React Web UI** locally.
The user explicitly requested core/UI now; the earlier requirement to wait for
live credentials before those phases was superseded for local development.
Live Telegram/Google, Docker runtime and Ubuntu reboot acceptance remain pending.
No VPS upload occurred.

## Delivered

SQLite WAL metadata, dedupe, transactional persistent/fair priority queue;
paged history checkpoints, incremental/recent reconciliation, live/edit listener;
Telethon and storage adapters; streaming rcat crypt, plaintext SHA-256,
verification/promotion/conflict handling; retry/FloodWait, cancellation and recovery;
CLI; daily DB snapshots; authenticated cursor REST API; React/TypeScript UI for
Dashboard, Sources, Topics, Transfers, Library, Failed, Storage and Settings,
responsive dark/light; Docker/Compose+Caddy, systemd and source-only release.

## Acceptance evidence

- 22 backend tests PASS, using isolated SQLite + actual rclone local crypt.
- Hard SIGKILL at 10%, 50%, 90% kills isolated service/rclone process group;
  restart succeeds, one job remains, no premature COMPLETED, DB integrity and
  decrypted final SHA-256 match.
- Crash window after final promotion before DB commit reconciles by stored digest;
  existing conflict never overwritten; truncated stream never completes.
- Persisted FloodWait 300 seconds prevents a second API request after new rate
  controller construction. Repeated waits test no early retry.
- Simulated storage Google 429 persists a storage pause and retry, no false upload.
- Auth/no-auth, HttpOnly cookie, CSRF/origin, login rate limiting, chunked body limit,
  pagination, source removal preservation, Unicode/topic mapping tests PASS.
- Browser E2E PASS: login, discover/add source, topics, persisted settings, real
  local encrypted jobs, reconciliation, live event injection, library/hash detail,
  desktop/mobile layout and no browser JS errors. Screenshots inspected.
- TypeScript/Vite production build and Python Ruff lint PASS.
- Lazy 500,000 messages / 50,000 media: 37.62s, peak RSS 69,074,944 B (~65.9 MiB),
  RAM growth 3,866,624 B (~3.7 MiB), SQLite main file 44,093,440 B. Metadata test only.
- Original phase-0 10 GiB crypt roundtrip: 93.369s, Python+rclone peak
  150,781,952 B (~143.8 MiB), full decrypted SHA-256 matched. Original POC includes
  one hash read; core full verification reads temporary and final separately.

Actual engine one/two-worker results are in PERFORMANCE.md and private
`data/reports/workers.json`. No synthetic result claims Telegram/Google throughput.

## Spec section 128 — actual answers

| # | Question | Implementation |
|---|---|---|
| 1 | Library | Telethon 1.45.0; bounded async chunks, persistent session, FloodWait and raw forum APIs. TDLib/Pyrogram decision in TELEGRAM-ARCHITECTURE.md. |
| 2 | Byte route | iter_download → ≤512 KiB bytes → shared download limiter → SHA-256 → asyncio subprocess stdin/drain → rclone rcat → crypt → storage. |
| 3 | Full plaintext on VPS | Never written by streaming implementation; decrypt verification also hashes stdout without a full file. Real cloud backend behavior still needs acceptance. |
| 4 | One-worker peak RAM | Original POC ~143.8 MiB at 10 GiB. Actual core worker measured separately in PERFORMANCE.md; not Linux/real Telegram performance. |
| 5 | Streaming peak disk | Worker benchmark measures operational disk excluding ciphertext test backend. No plaintext spool. Installed runtimes/source, SQLite/logs/backups add fixed/growing metadata footprint; target VPS measurement pending. |
| 6 | 100 GB with 5 GB free | Architecture is bounded by chunks rather than payload size, but a 100 GB real Telegram transfer is not proven and depends on Telegram file availability, backend and quotas. No unsupported claim. |
| 7 | Fail at 99% | RETRY_WAIT with backoff; incomplete UUID never final. Retry from byte zero unless an uploaded known object with saved digest can be validated. |
| 8 | Reboot at 99% | Startup converts interrupted TRANSFERRING/VERIFYING to retry/cancel intent. Worker reconciles saved temporary/final via size+hash; unknown data is not completed. Hard-kill tests pass locally. |
| 9 | FloodWait 300s | Persist account-wide epoch deadline ≥300s plus safety second, no new API attempts until expiry; does not consume retry budget. Pace reduced after waits. |
| 10 | Google 429 | Safe classified error, account storage pause + exponential jitter backoff, job RETRY_WAIT or FAILED after retry threshold; no concurrency increase. |
| 11 | Duplicate prevention | SQLite unique chat/message/media-index/file-id revision; unique media job, atomic claim/checkpoint, stored stable remote path and digest. |
| 12 | Topic identity | Telegram topic/root message ID (General 1, normal group 0), extracted from forum reply header; source identified by numeric chat ID. |
| 13 | Topic rename | Updates display name; persisted path component is not rewritten. Existing media paths and identity remain stable. |
| 14 | Message delete | Backup kept; delete events ignored. Old media revision also retained. |
| 15 | Browser closed | Backend scanner/workers continue. Browser is only the authenticated control/monitor client. |
| 16 | rclone credentials | Private RCLONE_CONFIG, mode 600. Docker /config/rclone/rclone.conf mount; never frontend/image/Git. |
| 17 | Session | Private TELEGRAM_SESSION_PATH, default data/session/account.session; Docker /data/session/account.session. Umask 077; independent from web session. |
| 18 | SHA-256 | Updated per plaintext input chunk inside StorageProvider.put_stream; stored on media before VERIFYING. |
| 19 | Verify | Stream exact length, rclone success, logical stat; full mode temporary decrypted hash → immutable promotion → final size/hash; recovery always requires known hash. Size-only option is explicit. |
| 20 | Restore | Consistent SQLite snapshot + same crypt config/keys/remote/root + separately restored/new account session, permissions, init-admin session revocation, startup reconciliation and remote scan. BACKUP-RECOVERY.md gives steps. |

## Boundaries

Core supports streaming mode only. Cache mode/adaptive transfers, notification
webhooks, time scheduling, adaptive concurrency, cloud DB snapshots and Encrypted
Web Drive integration are follow-up phases from the spec, not silently claimed.
UI states Google independent wire progress/speed and quota as unavailable rather
than fake bars. Upload totals mean confirmed completed logical payload, not raw
network bytes/retries. Incomplete remote attempts are retained for review; old
attempt objects may be detected as unexpected and are never auto-deleted.

Real account login persistence/discovery/topics, actual cloud 5–10 GB acceptance,
Linux/Docker memory/disk and reboot tests require the corresponding environment.
The application currently runs at http://127.0.0.1:8787 with mock Telegram and local
crypt; private credentials are in data/local-access.txt.
