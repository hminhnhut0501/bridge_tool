# Phase 5: Customer/group entitlement resolver

The resolver collapses multiple historical orders into one current answer for
`telegram_user_id + group_code`.

Precedence:

1. Lifetime entitlement.
2. Timed active entitlement with the furthest expiry.
3. No active entitlement.

An old expired order must not be kicked when another active entitlement exists
for the same customer and group. The resolver is pure and performs no writes
or Telegram calls.
