# Phase 2: Canonical plan completion

Run the verification SQL after the canonical migrations. The result must make
the following distinction explicit:

- supported family + duration + group: eligible for entitlement backfill;
- `UNSUPPORTED`: retained for history and excluded from kick;
- `REVIEW`: incomplete mapping or duration, excluded from kick;
- cancelled rows: no active entitlement is created;
- timed PAID/EXPIRED rows without expiry: not backfilled.

Do not rename or overwrite `plan_name`. Canonical columns are the only fields
allowed in the new entitlement pipeline.
