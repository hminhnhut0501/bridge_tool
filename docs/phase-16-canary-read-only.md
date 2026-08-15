# Phase 16: Canary Read-Only

## Configuration

```text
RENEWAL_NEW_CORE_CANARY=ON
RENEWAL_NEW_CORE_DRY_RUN=ON
```

With both flags enabled, scheduler uses `run_read_only_cycle()`.

## Guarantees

- No order status update.
- No task/group task update.
- No Telegram ban/unban/restrict.
- No legacy support event write.
- Membership lookup is read-only.

The canary reports order/task/group counts and membership outcomes for
comparison against the baseline. It must run for a complete expiry window
before mutation is considered.

## Rollback

```text
RENEWAL_NEW_CORE_CANARY=OFF
```
