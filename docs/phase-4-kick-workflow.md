# Phase 4: Kick Workflow

Status: implemented on 2026-08-15

## Responsibility

`new_core/kick_workflow.py` owns group-task execution only:

- skip resolved/non-due tasks;
- retain access when another active order grants the same group;
- check Telegram presence;
- execute a kick through `MembershipGateway`;
- move the task to confirmation, retry, blocked, or review state.

It does not know Supabase, Google Sheets, `scheduler.py`, `web_backend.py`, or
`support_events`.

## Safety behavior

- Active-order checks happen before any Telegram mutation.
- Unknown membership confirmation goes to `review_required`, never to `done`.
- Telegram failure becomes `retry_scheduled`.
- A successful kick becomes `waiting_confirm`; the next run confirms absence.
- State changes are validated by the Phase 1 state machine.

## Deferred integration

The existing `scheduler_kick_workflow.py` remains the compatibility production
path. Phase 5 will wire production adapters and make the scheduler delegate to
this workflow after async worker/lock semantics are finalized.
