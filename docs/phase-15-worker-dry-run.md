# Phase 15: Worker Dry-Run

Status: implemented on 2026-08-15

## Behavior

`renewal_worker_dry_run.py` evaluates processing group tasks without changing
state or mutating Telegram:

```text
present + no active order -> would_kick
absent                   -> confirm_done
active order             -> retain_active_order
unknown membership      -> review_unknown_membership
missing plan mapping    -> review_mapping_unavailable
```

## Safety gate

Any missing plan mapping blocks the action. It is never interpreted as “no
active order”. This is required while Phase 14 reports unresolved production
mapping.

## Production status

The script is ready to run read-only. Do not enable mutation until
`plan_mapping_unavailable = 0` and the dry-run output has been reviewed.
