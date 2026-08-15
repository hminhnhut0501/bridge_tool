# Phase 21: Stabilize Tooling and Runtime

## Implemented

- Shared read-only HTTP client with bounded retries, exponential backoff and
  explicit `ReadonlyHttpError`.
- Supabase snapshot and Telegram membership audit use the shared client.
- Runtime check reports required environment keys, Python version and
  `requests` availability without printing secret values.
- Existing `requirements.txt` already declares `requests==2.31.0`; deployment
  must install it instead of relying on the local machine environment.

## Gate

Run:

```bash
python3.11 -m scripts.runtime_check
```

Then run the read-only snapshot/audit scripts. A failed HTTP request must
produce a non-zero exit code and a clear error, never an empty successful
report.
