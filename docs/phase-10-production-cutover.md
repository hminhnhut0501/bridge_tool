# Phase 10: Production Cutover Checklist

The code-side hardening is complete. Production cutover remains gated by
external environment access and a UI parity decision.

## Ready in code

- Structured renewal metrics are emitted by the scheduler canary log.
- Group planner expands expired parent tasks into v2 group tasks.
- Read-only baseline builder exists in `renewal_baseline.py`.
- Feature flag has an immediate rollback path: set
  `RENEWAL_NEW_CORE_CANARY=OFF`.
- Python and frontend validation are green.

## Production procedure

1. Fetch orders, parent tasks, group tasks, and support-log counts read-only.
2. Store the output of `build_renewal_baseline()` as the migration snapshot.
3. Run canary with `RENEWAL_NEW_CORE_CANARY=ON` in dry-run/no-mutation mode.
4. Compare expired orders, created tasks, group expansion, review rate, and
   retry rate against the snapshot.
5. Enable Telegram mutation only after group-task parity is confirmed.
6. Monitor structured cycle logs for at least one full expiry window.
7. Roll back by setting the flag `OFF` if review/error/stale-task thresholds are
   exceeded.

## Explicitly not claimed

This repository change does not enable a production environment variable, run
Supabase production queries, or delete the old renewal JSX. Those actions need
the production deployment context and a completed UI parity check. The current
`page.tsx` renewal block remains the safe fallback until the replacement
component renders all table, timeline, and mutation actions.
