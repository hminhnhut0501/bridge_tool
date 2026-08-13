# Renewal Kick V2 Pseudo-code

This file mirrors the current `scheduler.py` flow and shows how to split the renewal kick system into:

- task table
- group task table
- attempt audit table
- scheduler / worker / finalizer responsibilities

## Current entrypoints to replace gradually

- `enqueue_expired_renewal_kick_tasks(...)`
- `process_due_renewal_kick_tasks(...)`
- `ensure_member_kicked(...)`
- `member_is_present(...)`
- `renewal_kick_state(...)`
- support-event fallback logic in `scheduler.py`

## Phase 1 - Scheduler writes v2

```python
def enqueue_expired_renewal_kick_tasks_v2(order, now):
    task = upsert_task_v2(order)
    groups = resolve_kick_groups(order.plan_name)

    if not groups:
        mark_task_review_required(task, reason="group_unmapped")
        return task

    for group in groups:
        upsert_group_task_v2(task, group)
        upsert_legacy_map(order, group, source="scheduler")

    recalc_task_counters(task.id)
    return task
```

## Phase 2 - Worker claims group tasks

```python
def process_due_renewal_kick_group_tasks_v2(now):
    group_tasks = claim_due_group_tasks(now, limit=50)

    for gt in group_tasks:
        if gt.group_state in TERMINAL_GROUP_STATES:
            continue

        if has_active_order_elsewhere(gt.telegram_user_id, gt.order_id, gt.group_id):
            update_group_task(gt, state="blocked_active_order", reason="active_order_retained")
            append_attempt(gt, action="skip", actor="worker", reason_code="active_order_retained")
            continue

        try:
            update_group_task(gt, state="processing", locked_at=now, locked_by="worker")
            append_attempt(gt, action="kick", actor="worker", attempt_state="claimed", reason_code="kick_attempt")

            result = telegram_kick_member(gt.group_id, gt.telegram_user_id)
            if result.ok:
                update_group_task(
                    gt,
                    state="waiting_confirm",
                    next_retry_at=now + timedelta(seconds=30),
                    last_reason="kick_sent",
                )
                append_attempt(gt, action="kick", actor="worker", attempt_state="kick_sent", reason_code="kick_sent")
            else:
                schedule_retry_or_review(gt, result.error_code, result.error_message)
        except Exception as exc:
            schedule_retry_or_review(gt, "bot_api_error", str(exc))
```

## Phase 3 - Finalizer confirms state

```python
def finalize_due_group_tasks_v2(now):
    group_tasks = load_group_tasks_due_for_confirm(now)

    for gt in group_tasks:
        if gt.group_state not in {"waiting_confirm", "retry_scheduled", "processing"}:
            continue

        try:
            member = telegram_check_member(gt.group_id, gt.telegram_user_id)

            if member is False:
                update_group_task(gt, state="kicked", completed_at=now, last_reason="kick_confirmed")
                append_attempt(gt, action="confirm", actor="finalizer", attempt_state="confirm_passed", reason_code="kick_confirmed")
            elif member is True:
                if gt.attempt_count >= MAX_GROUP_ATTEMPTS:
                    update_group_task(gt, state="review_required", resolved_at=now, review_reason="max_retry_reached")
                    append_attempt(gt, action="review", actor="finalizer", attempt_state="review_required", reason_code="retry_limit_reached")
                else:
                    schedule_retry(gt, reason="still_present_after_confirm")
            else:
                if gt.confirm_count >= MAX_CONFIRM_ATTEMPTS:
                    update_group_task(gt, state="review_required", resolved_at=now, review_reason="confirm_unknown")
                    append_attempt(gt, action="review", actor="finalizer", attempt_state="review_required", reason_code="confirm_timeout")
                else:
                    schedule_retry(gt, reason="confirm_unknown")
        except Exception as exc:
            if is_transient(exc) and gt.confirm_count < MAX_CONFIRM_ATTEMPTS:
                schedule_retry(gt, reason="bot_api_error")
            else:
                update_group_task(gt, state="review_required", resolved_at=now, review_reason="finalizer_exception")
                append_attempt(gt, action="review", actor="finalizer", attempt_state="failed_exception", reason_code="bot_api_error")
```

## Phase 4 - Reconcile parent task

```python
def reconcile_parent_task_v2(task_id):
    groups = list_group_tasks(task_id)

    kicked = count(groups, lambda g: g.group_state == "kicked")
    retained = count(groups, lambda g: g.group_state == "retained")
    blocked = count(groups, lambda g: g.group_state == "blocked_active_order")
    pending = count(groups, lambda g: g.group_state in {"pending", "selected", "processing", "waiting_confirm", "retry_scheduled"})
    review = count(groups, lambda g: g.group_state == "review_required")

    if pending > 0:
        task_state = "partial_done" if kicked > 0 else "running"
    elif review > 0:
        task_state = "review_required"
    elif blocked > 0 and kicked == 0:
        task_state = "blocked"
    elif kicked > 0 and review == 0 and pending == 0:
        task_state = "done"
    else:
        task_state = "failed_terminal"

    update_task_summary(task_id, task_state, kicked, retained, blocked, pending, review)
```

## Phase 5 - Migration mapping rules

```python
def map_legacy_state_to_v2(legacy_task):
    state = legacy_task.state.lower()
    last_error = legacy_task.last_error or ""

    if state in {"done", "member_kick_closed"}:
        return "kicked"
    if state in {"blocked_active_order"}:
        return "blocked_active_order"
    if state in {"pending_confirm", "processing"} and not last_error:
        return "waiting_confirm"
    if state in {"retry_pending", "error_retryable"}:
        return "retry_scheduled"
    if state in {"review_required"}:
        return "review_required"
    return "review_required"
```

## Phase 6 - Legacy fallback removal

- keep support-events as audit only
- stop using support-events to decide kick state
- all UI state should read from v2 tables first
- only fallback to legacy rows when v2 data is missing

## Notes for current codebase

- Keep `support_events` writes for human audit during transition
- Move decision-making into v2 tables only
- Use `metadata.reason` and `last_error` as the main support-debug surface
- Do not allow `pending_confirm` to survive beyond the hard confirm window
