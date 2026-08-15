# Phase 12: Migration Contract

Status: dry-run implemented on 2026-08-15

## Automatic mappings

Parent task:

```text
running       -> processing
retry_pending -> processing
pending_confirm -> processing
```

Group task:

```text
selected  -> processing
running   -> processing
unmapped  -> review_required
```

Canonical states are preserved as-is.

## Manual review

Unknown states are never written automatically. Stale `processing` and
`waiting_confirm` tasks must be handled by Phase 13 membership audit, not by
this migration.

## Safety

`scripts/renewal_state_migration_dry_run.py` is read-only. It reports aggregate
mapping counts for an operator-controlled migration plan, but does
not issue Supabase PATCH/POST requests and never calls Telegram.
