# Phase 3: Historical Repair Candidates

Phase 3 produces a read-only report from the state ledger and membership
audit. Only tasks whose Telegram membership is explicitly `absent` are marked
as eligible for a future repair operation. `unknown`, missing-order, orphan,
stale-lock, and duplicate records remain manual-review candidates.

Generate it with:

```bash
python3.11 -m scripts.renewal_historical_repair_candidates \
  /tmp/renewal-state-ledger.json \
  --membership-audit /tmp/stale-membership-audit-final.json \
  --output /tmp/renewal-historical-repair-candidates.json
```

This phase performs no Supabase write and no Telegram mutation.
