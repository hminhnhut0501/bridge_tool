# Phase 5: Worker Dry-run

The worker dry-run evaluates the same identity, plan-mapping, active-order,
and membership guards used by the worker, but never claims or updates a task
and never calls Telegram mutation methods.

```bash
python3.11 -m scripts.renewal_worker_dry_run > /tmp/renewal-worker-dry-run.json
```

The report contains per-task planned outcomes and must show zero Supabase
writes and zero Telegram mutations before any cohort mutation is considered.
