# Phase 4: Entitlement backfill production

Run the controlled backfill only after Phase 2 canonical verification and
Phase 3 group mapping verification pass.

After migration, run the verification SQL and require:

```text
duplicate_entitlement_keys = 0
invalid_timed_entitlements = 0
unsupported_kickable_entitlements = 0
```

`REVIEW` and `CANCELLED` rows are expected to remain outside automatic kick.
The backfill must not create Telegram mutations or legacy tasks.
