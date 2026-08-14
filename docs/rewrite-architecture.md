# Rewrite Architecture

This document describes the target architecture for the renewal/expiry/kick system.

## Layers

### 1) Core

Pure business rules with no DB, Telegram, or web dependencies.

Responsibilities:
- Determine whether an order is active or expired.
- Determine whether an order should be reconciled to `EXPIRED`.
- Determine kick eligibility from order state and membership state.
- Define the canonical renewal kick state machine.

Files:
- `new_core/expiry.py`
- `new_core/kick.py`
- `new_core/models.py`

### 2) Workflow

Application orchestration. This layer coordinates core decisions with side effects.

Responsibilities:
- Scan for expired orders.
- Enqueue renewal kick work.
- Claim and process kick tasks.
- Finalize task/group state.
- Reconcile stale states.

Files:
- `new_core/workflow.py`
- `new_core/reconcile.py`

### 3) Adapters

Infrastructure and integration points.

Responsibilities:
- Read/write Supabase.
- Read/write support_events.
- Talk to Telegram.
- Expose admin web/API views.
- Start background workers.

Files:
- `supabase_store.py`
- `scheduler.py`
- `web_backend.py`
- `processor.py`
- `main.py`
- `order_expiry_workers.py`
- `kick_state_service.py`

## File Map

### Keep
- `supabase_store.py`
- `processor.py`
- `main.py`
- `bot_instance.py`
- `support_utils.py`
- `hidden_group_utils.py`
- `config_utils.py`
- `database.py`

### Cut next
- `scheduler.py`
- `web_backend.py`
- `kick_state_service.py`
- `order_expiry_workers.py`

### Replace
- Kick/expiry decision logic in `scheduler.py` should be replaced by `new_core/*`.
- Admin kick/audit synthesis in `web_backend.py` should be replaced by `new_core/workflow.py` consumers.

## Migration Rule

New code should depend on `new_core` first.
Old code may call into `new_core` while migration is in progress.
No new business rule should be added directly into `scheduler.py` or `web_backend.py`.
