# Phase 3: Entitlement data-quality audit

Run the audit only after `customer_entitlements_v1` exists in Supabase:

```bash
python3.11 -m scripts.entitlement_audit \
  --output /tmp/entitlement-audit.json
```

The report separates `REVIEW` from safe expired entitlements. No row is
automatically repaired, no task is created, and no Telegram mutation occurs.

Only an `EXPIRED` entitlement with a canonical group and `VERIFIED` source
quality becomes a future kick candidate. Missing expiry, unsupported plans,
missing group mapping, and legacy ambiguity remain review-only.
