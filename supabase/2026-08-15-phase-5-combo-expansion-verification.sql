-- Phase 5: Combo expansion verification. Read-only.

select
    source_order_id,
    telegram_user_id,
    count(*) filter (where group_code in ('PRIME', 'BOY', 'REAL', 'ASIA')) as child_count,
    count(*) filter (where group_code = 'COMBO_FULL') as parent_count
from public.customer_entitlements_v2
where source_order_id in (
    select source_order_id
    from public.customer_entitlements_v2
    where group_code = 'COMBO_FULL'
)
group by source_order_id, telegram_user_id
order by source_order_id;

select count(*) as incomplete_combo_expansions
from (
    select source_order_id
    from public.customer_entitlements_v2
    where group_code in ('PRIME', 'BOY', 'REAL', 'ASIA')
    group by source_order_id
    having count(distinct group_code) <> 4
) incomplete;

select count(*) as combo_parent_jobs
from public.entitlement_kick_jobs j
join public.customer_entitlements_v2 e on e.id = j.entitlement_id
where e.group_code = 'COMBO_FULL';

select
    e.group_code,
    e.group_id,
    count(*) as child_count
from public.customer_entitlements_v2 e
where e.group_code in ('PRIME', 'BOY', 'REAL', 'ASIA')
group by e.group_code, e.group_id
order by e.group_code, e.group_id;
