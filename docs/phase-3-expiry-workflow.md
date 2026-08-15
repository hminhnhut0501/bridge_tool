# Phase 3: Expiry Workflow

Status: implemented on 2026-08-15

## Responsibility

`new_core/expiry_workflow.py` owns only:

1. loading expiry candidates through `OrderRepository`;
2. classifying them through the core expiry contract;
3. reconciling `PAID` to `EXPIRED`;
4. creating one v2 kick task per order.

It does not call Telegram, send notifications, read `support_events`, or
perform membership checks.

## Idempotency

The workflow checks `(order_id, telegram_user_id)` through
`KickTaskRepository.get_task()` before creating a task. Re-running the scan
does not create another task and does not rewrite an already `EXPIRED` order.

## Safety rules

- Lifetime plans are never expired by this workflow.
- Active or non-paid orders are skipped.
- Missing order/user identity is counted as invalid and is not written.
- Only a normalized `expired` result may reach reconciliation.
- The order transition is validated through Phase 1 state machine.

## Deferred work

The existing `scheduler_expiration_workflow.py` remains a compatibility path.
Phase 5 will make scheduler call this workflow directly after production
Supabase adapters are introduced and reminder delivery is split out.
