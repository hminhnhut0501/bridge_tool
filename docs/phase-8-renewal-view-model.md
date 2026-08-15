# Phase 8: Renewal View-Model

Status: implemented on 2026-08-15

## Contract

`new_core/renewal_view_model.py` exposes a stable, task-first response:

- `schema_version`
- `summary`
- `rows`

Each row contains order state, normalized task state, group counters, next
action, blocker reason, latest attempt, last error, and update timestamp.

The UI does not infer kick eligibility from raw order dates, group states, or
support events. It renders `next_action` and the supplied reason.

## State source priority

1. order state comes from the core expiry contract;
2. task state comes from v2 task/group state;
3. attempts are display-only diagnostics;
4. `support_events` is intentionally absent.

The existing admin view service remains a compatibility consumer until the
backend route is migrated to this schema in the next UI phase.
