# Phase B: Controlled entitlement backfill

The migration copies only orders that have:

- status `PAID` or `EXPIRED`;
- a canonical family other than `UNSUPPORTED`;
- a canonical duration other than `REVIEW`;
- a canonical group code;
- an expiry for timed plans.

Cancelled orders, Signature/unsupported plans, missing-expiry rows, and other
ambiguous records are intentionally excluded. They do not become kick jobs.

The migration is idempotent and creates no Telegram or kick-task mutation.
