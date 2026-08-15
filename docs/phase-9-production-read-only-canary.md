# Phase 9: Production read-only canary

Run with production environment variables loaded:

```bash
python3.11 -m scripts.renewal_kick_canary_v2 \
  --limit 20 \
  --timeout 20 \
  --retries 4 \
  --output /tmp/renewal-kick-canary-v2.json
```

Run at least three cycles. The command reads Supabase and Telegram membership
only. It cannot call `kick()` and writes no Supabase state.

Before limited mutation, require:

- no unexpected `REVIEW` or `UNKNOWN`;
- no duplicate jobs;
- no eligible job missing `group_id`;
- sampled `WOULD_KICK` rows are correct;
- `telegram_mutation_count = 0` for every canary report.
