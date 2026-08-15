# Phase 13: Stale Task Membership Audit

Status: read-only audit implemented on 2026-08-15

## Classification

Each stale `processing` group task is classified through Telegram
`getChatMember`:

```text
left/kicked/not found -> absent
member/admin/creator  -> present
timeout/API ambiguity -> unknown
```

## Safety

- No Supabase PATCH/POST.
- No Telegram ban/unban/restrict.
- No support event write.
- Output is aggregate-only; identifiers are not printed.

## Follow-up policy

- `absent`: eligible for controlled `done/kicked` reconciliation after review.
- `present`: must be checked against active-order membership before retry.
- `unknown`: must become `review_required`, never auto-complete.

The audit result must be reviewed before any state mutation is performed.
The production script uses a bounded eight-worker read-only pool to avoid a
single slow Telegram request blocking the entire audit.
