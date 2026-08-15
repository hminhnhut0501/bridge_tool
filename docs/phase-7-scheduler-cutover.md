# Phase 7: Scheduler Cutover

Status: canary entrypoint implemented on 2026-08-15

## What changed

- `scheduler_new_core_runtime.py` builds the new-core runtime from production
  adapters.
- `scheduler.check_expirations_professional()` can select the new runtime with
  `RENEWAL_NEW_CORE_CANARY=ON`.
- The flag defaults to `OFF`, so the current production path is unchanged.
- The old path remains an immediate rollback by switching the flag off.

## Safety gate

The canary is intentionally not the production default yet. The new expiry
workflow currently creates the parent kick task, while production group-plan
expansion still lives in the compatibility workflow. Turning the flag on
before that planner is moved would produce incomplete group-task coverage.

## Required before enabling

1. Move plan-to-group expansion into a repository/policy adapter.
2. Add integration tests proving every expired order has the expected group tasks.
3. Compare old/new counts for expired orders, queued tasks, and group tasks.
4. Run canary read-only/dry-run before allowing Telegram mutations.
5. Enable for a small cohort, monitor review/error rates, then make it default.
