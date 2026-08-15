# Phase A: Entitlement normalization

The rebuilt kick flow uses `customer_entitlements_v2` as its only entitlement
source. Each row represents one order granting access to one canonical group.

Identity:

```text
source_order_id + group_code
```

Required behavior:

- timed entitlements require `expires_at`;
- lifetime entitlements may omit `expires_at`;
- unsupported or ambiguous plans are not inserted as kickable entitlements;
- duplicate source order/group rows are rejected;
- this phase creates the contract only and does not copy legacy data.
