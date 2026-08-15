# Phase E: Bounded safety sweep

The safety sweep is a recovery mechanism for delayed jobs missed during a
restart or outage. It only reads due `PENDING` and `RETRY` jobs, orders by the
oldest `run_at`, and processes at most 20 rows per invocation.

Retry delays are capped at:

```text
1 minute -> 5 minutes -> 15 minutes -> REVIEW
```

The sweep never scans `orders`, never creates duplicate jobs, and never runs a
permanent loop. It is safe to invoke from a periodic platform scheduler.
