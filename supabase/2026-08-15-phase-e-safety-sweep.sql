-- Phase E: bounded safety sweep query.
-- This is intentionally a read-only query. The worker owns mutations.

select
    id,
    entitlement_id,
    source_order_id,
    telegram_user_id,
    group_code,
    group_id,
    run_at,
    status,
    attempts
from public.entitlement_kick_jobs
where status in ('PENDING', 'RETRY')
  and run_at <= now()
order by run_at asc
limit 20;
