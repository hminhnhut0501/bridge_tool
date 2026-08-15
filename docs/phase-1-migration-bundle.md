# Phase 1: Migration bundle

## Required order

Run the migrations in this order:

1. `2026-08-15-phase-a-entitlement-contract.sql`
2. `2026-08-15-phase-c-group-mapping.sql`
3. `2026-08-15-phase-b-backfill-entitlements.sql`
4. `2026-08-15-phase-c-expand-combo-entitlements.sql`
5. `2026-08-15-phase-c-kick-jobs.sql` if the job table was not created by the expand migration

The expand migration is self-contained for the job table, so it may be run
after the backfill and group map even when the standalone job migration was
skipped.

## Verification

Run `2026-08-15-phase-1-migration-verification.sql` after the bundle.

Expected invariants:

- all three required tables exist;
- invalid timed entitlements are zero;
- duplicate entitlement keys are zero;
- duplicate job keys are zero;
- verified entitlements missing group IDs are zero except explicitly scoped Combo parents;
- no job points to a lifetime or review entitlement.

All migrations are expected to be rerunnable without creating duplicate rows.
