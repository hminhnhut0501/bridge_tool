-- Phase 2: canonical plan verification. Read-only.

select
    canonical_plan_family,
    canonical_duration,
    canonical_group_code,
    count(*) as order_count
from public.orders
group by canonical_plan_family, canonical_duration, canonical_group_code
order by canonical_plan_family, canonical_duration, canonical_group_code;

select order_id, plan_name, status, canonical_plan_family,
       canonical_duration, canonical_group_code
from public.orders
where canonical_plan_family is null
   or canonical_duration is null
   or canonical_group_code is null
   or canonical_plan_family = 'UNSUPPORTED'
   or canonical_duration = 'REVIEW'
order by created_at nulls last, order_id;

select count(*) as invalid_timed_orders
from public.orders
where canonical_duration <> 'LIFETIME'
  and canonical_duration is not null
  and canonical_duration <> 'REVIEW'
  and expire_at is null
  and upper(coalesce(status, '')) in ('PAID', 'EXPIRED');

select count(*) as signature_not_isolated
from public.orders
where plan_name ilike '%signature%'
  and coalesce(canonical_plan_family, '') <> 'UNSUPPORTED';
