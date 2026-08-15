# Phase 2: Entitlement projection

The canonical source for renewal decisions is now the read-only view
`public.customer_entitlements_v1`. It projects orders into a small contract:

- customer and source order
- canonical plan and group
- start and expiry timestamps
- `ACTIVE`, `EXPIRED`, `CANCELLED`, or `REVIEW`
- a machine-readable reason and source quality

No task is created in this phase. `REVIEW`, `UNSUPPORTED`, missing expiry, and
missing group mapping are never eligible for automatic kick.
