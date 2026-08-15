# Phase 0: Scope freeze

## Product rule

An entitlement that has expired and has no newer active entitlement for the
same customer and target group may be kicked from that group.

## Sources of truth

The new flow reads only:

- `customer_entitlements_v2` for access rights;
- `entitlement_kick_jobs` for delayed work;
- the Telegram membership adapter for current membership.

## Explicitly out of scope

The new kick decision must not read or mutate through:

- `support_events`;
- `renewal_kick_tasks_v2`;
- scheduler legacy state;
- admin UI state;
- raw `plan_name` heuristics.

## Single mutation path

The only allowed mutation path is:

```text
entitlement_kick_jobs
-> one-shot worker
-> membership adapter
-> bounded Telegram kick
```

## Frozen states

Entitlements:

```text
ACTIVE, EXPIRED, CANCELLED, REVIEW
```

Jobs:

```text
PENDING, PROCESSING, DONE, RETAINED, SKIPPED, RETRY, REVIEW
```

## Change control

No new state, fallback source, automatic backfill rule, or mutation path may
be added without updating this contract and its tests. Legacy remains
read-only until the sunset gate passes.
