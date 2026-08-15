# Order lifecycle repair review

## Scope

The production audit found 8 `PAID_BUT_EXPIRED_BY_DATE` orders and 197
orders with a missing `expire_at`.

## Findings for the 8 PAID rows

Six rows have a newer PAID order for the same customer with a future expiry.
They must remain untouched because the old order can be historically expired
while the customer is currently active:

- `1782823326834`
- `1782196901605`
- `1782257724182`
- `1782714519253`
- `1783177538186`
- `1782960620581`

Two rows have no newer PAID order and are safe status-repair candidates,
subject to the guarded SQL predicate:

- `1782656343842`, user `7759732416`, expired `2026-07-28T14:19:03+00:00`
- `1782123274164`, user `949510415`, expired `2026-07-22T10:14:34+00:00`

The migration only changes `PAID` to `EXPIRED` when the row is still expired
and no other PAID order for that customer has a future expiry.

## Findings for the 197 missing-expiry rows

These are not safe for bulk expiry backfill:

- `CANCELLED` rows should keep `expire_at = null`; they did not establish active access.
- Historical `EXPIRED` rows lack sufficient evidence to reconstruct the original expiry.
- Any lifetime row with no expiry is valid by design.
- The unmapped plan `VIP 1 Tháng - Hang Cú Signature Việt Nam` needs explicit plan mapping before any lifecycle decision.

Therefore the supplied migration is read-only for this population. A future
backfill must use a trusted payment/activation timestamp and an explicit
duration contract, not a guessed default.

## Runbook

1. Run `2026-08-15-audit-missing-expire-at.sql` in Supabase SQL Editor and export the result.
2. Run `2026-08-15-fix-paid-expired-order-status.sql`; it may return 2 rows on the first run or 0 rows if the repair was already applied.
3. Confirm both target IDs are `EXPIRED` after the migration.
4. Re-run `python3.11 -m scripts.order_lifecycle_audit` and confirm the PAID stale count is zero or only contains rows with an active newer order.
