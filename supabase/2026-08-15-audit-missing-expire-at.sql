-- Read-only audit for orders with no expire_at.
-- No data is changed. Do not infer a 30-day expiry from plan_name alone.

select
    order_id,
    telegram_user_id,
    plan_name,
    status,
    paid_at,
    created_at,
    canonical_plan_family,
    canonical_duration,
    canonical_group_code
from public.orders
where expire_at is null
order by created_at nulls last, order_id;

select
    upper(coalesce(status, 'NULL')) as status,
    canonical_plan_family,
    canonical_duration,
    count(*) as order_count
from public.orders
where expire_at is null
group by 1, 2, 3
order by 1, 2, 3;
