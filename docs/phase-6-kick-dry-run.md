# Phase 6: Kick dry-run

This phase connects the entitlement projection, customer/group resolver, and
kick policy. It produces a report only.

Possible decisions:

- `KICK`: verified expired entitlement with no newer active entitlement.
- `BLOCK`: a newer active entitlement protects the customer.
- `REVIEW`: mapping or expiry data is incomplete.
- `NOOP`: not an expiry candidate.

The dry-run guarantees zero Supabase writes and zero Telegram mutations.
