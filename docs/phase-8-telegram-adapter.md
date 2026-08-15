# Phase 8: Telegram membership adapter

The adapter has conservative semantics:

- member status `member`, `restricted`, `administrator`, `creator` -> present;
- `left`, `kicked`, `banned` -> absent;
- timeout, rate limit, permission errors, and unknown errors -> unknown/retry;
- only a proven `user not found`/`participant_id_invalid` response is absent.

The kick operation is idempotent through ban followed by unban. Adapter errors
are classified without exposing raw exception text to job state.
