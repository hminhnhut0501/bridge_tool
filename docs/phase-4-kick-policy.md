# Phase 4: Kick policy

The new kick policy is a pure decision function over an entitlement. It does
not read `support_events`, does not inspect UI state, and does not mutate
Telegram or Supabase.

Automatic kick requires all conditions:

- entitlement state is `EXPIRED`
- source quality is `VERIFIED`
- group code is present
- expiry is valid and is not in the future
- no newer active entitlement exists for the same customer/group

Everything else produces `REVIEW`, `BLOCK`, or `NOOP`. The mutation adapter is
deliberately deferred to a later phase.
