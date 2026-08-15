# Phase 18: Full worker cutover readiness

## Before cutover

- final product gate is `allowed: true`;
- three read-only canary cycles are archived;
- limited mutation has no incorrect kick;
- duplicate jobs are zero;
- legacy mutation count is zero;
- kill switch is tested;
- Supabase claim RPC is deployed;
- Telegram bot permissions are verified for every active group.

## Cutover order

1. Set legacy renewal mutation to read-only.
2. Stop legacy scheduler kick invocations.
3. Stop creation of new legacy kick tasks.
4. Keep legacy data available for audit.
5. Enable the new one-shot worker with batch 5 and concurrency 1.
6. Run one controlled production cycle.
7. Check metrics and job states.
8. Continue only if no safety counter increases.

## Rollback

1. Set `RENEWAL_KICK_ENABLED=false`.
2. Stop the external one-shot scheduler.
3. Do not reactivate legacy mutation automatically.
4. Leave `DONE` and `RETAINED` jobs unchanged.
5. Move uncertain jobs to `REVIEW` after investigation.

Full cutover is an operational action, not a code default. The repository must
keep mutation disabled by default.
