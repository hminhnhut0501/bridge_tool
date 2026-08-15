-- Phase 3: group mapping verification. Read-only.

select group_code, telegram_group_id, group_name, ordinal, is_active
from public.canonical_group_map
order by group_code, ordinal;

select group_code, count(*) as active_targets
from public.canonical_group_map
where is_active = true
group by group_code
order by group_code;

select
    e.group_code,
    count(*) as verified_missing_group_id
from public.customer_entitlements_v2 e
where e.source_quality = 'VERIFIED'
  and e.group_id is null
group by e.group_code
order by e.group_code;

select
    e.source_order_id,
    e.telegram_user_id,
    e.group_code,
    e.group_id
from public.customer_entitlements_v2 e
where e.source_quality = 'VERIFIED'
  and e.group_id is null
order by e.source_order_id, e.group_code;
