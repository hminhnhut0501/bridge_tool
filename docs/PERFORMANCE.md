# Performance evidence — local Mac, 2026-10-06

All payloads/metadata are synthetic. Crypt encryption and SQLite are real.
These measurements do not establish real Telegram/Google Drive throughput.

| Engine workers | Payload / worker | Duration incl. 2 hash passes | Aggregate payload rate | Peak Python+rclone RSS | Peak operational test disk |
|---|---|---|---|---|---|
| 1 | 256 MiB | 3.601 s | 71.1 MiB/s | 140.1 MiB | 366.4 KiB |
| 2 | 256 MiB | 3.535 s | 144.8 MiB/s | 187.3 MiB | 539.4 KiB |

RSS is sampled every 50 ms and sums the Python process plus children. It excludes
OS page cache and unrelated processes. Operational disk above is the isolated
runtime config/SQLite/WAL and excludes encrypted backend output, installed runtimes,
source, logs and snapshots. The local encrypted backend necessarily occupies payload
size; a Drive backend would store that ciphertext remotely.

One worker remains the default despite faster aggregate local two-worker results.
No Telegram account was stressed and no concurrency increase was deployed.

Original POC: 256 MiB → 151.2 MiB peak RSS; 10 GiB → 143.8 MiB, 93.369 s,
109.7 MiB/s whole-run average including one decrypt hash read. Both SHA-256 checks
match. Different sampled Go/Python allocation peaks are expected; RSS did not grow
with payload size in those runs. The core now performs two hash passes by default.

Large history: 500,000 lazy messages, 50,000 media/jobs, 37.62 s,
65.9 MiB peak RSS, 3.7 MiB RAM growth, 42.1 MiB main SQLite file.
Database/WAL disk grows with metadata; scanner RAM stays bounded by batches.

Frontend build: ~273 KiB JS (84 KiB gzip), ~30 KiB CSS (6.7 KiB gzip).
Frontend polls bounded pages; Google independent wire progress/speed is not available.

Reproduce: scripts/worker_benchmark.py, scripts/history_benchmark.py and
telegram-vault synthetic. Reports under data/reports. Tests create/delete only
their own isolated ciphertext backend. Linux/real account/cloud, free disk below
video size, 100 GB availability and VPS reboot remain separate acceptance items.
