# Phase 10: Limited mutation preflight

Run only after three clean read-only canary cycles:

```bash
python3.11 -m scripts.limited_mutation_preflight \
  /tmp/renewal-kick-canary-v2.json
```

The preflight enforces:

```text
batch <= 5
concurrency = 1
no REVIEW/UNKNOWN canary result
no duplicate jobs
no missing group IDs
```

It returns a non-zero exit code when mutation is unsafe. The command itself
never calls Telegram and never writes Supabase.
