# Phase 15: Release handover

## Required artifacts

- migration execution log;
- migration verification result;
- entitlement backfill report;
- Combo expansion report;
- kick job verification result;
- three read-only canary reports;
- limited mutation report;
- worker metrics snapshot;
- backend test output;
- frontend typecheck output;
- frontend build output;
- rollback confirmation.

## Final commands

```bash
git diff --check
python3.11 -m unittest discover -s tests -p 'test_*.py'
cd admin-ui && npm run typecheck && npm run build
```

## Production configuration

Keep mutation disabled until the release gate passes:

```text
RENEWAL_KICK_ENABLED=false
RENEWAL_KICK_BATCH=5
RENEWAL_KICK_CONCURRENCY=1
```

Enable mutation only as an explicit deployment operation after approval. The
application must retain a kill switch that can be changed without rebuilding.

## Rollback

1. Set `RENEWAL_KICK_ENABLED=false`.
2. Stop the one-shot scheduler invocation.
3. Leave completed jobs unchanged.
4. Mark only uncertain jobs `REVIEW` after investigation.
5. Keep legacy read-only for audit; do not reactivate legacy mutation blindly.

## Push policy

Do not commit `.env`, bot tokens, service-role keys, production dumps, or
temporary reports. Push only after the final product gate returns `allowed: true`.
