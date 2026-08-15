# Phase 9: Claim and Finalizer

Phase 9 defines the production state transition primitives without enabling
mutation. Every group task gets a deterministic idempotency key from
`order_id + group_id + telegram_user_id`, a lease when claimed, and a bounded
retry policy. Unknown outcomes become `review_required`; repeated failures
become `failed_terminal`.

The current implementation is pure and testable. The Supabase adapter must
next map claim to an atomic conditional update and attempts to a durable table
before limited mutation is enabled.
