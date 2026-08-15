-- Phase 4: entitlement backfill verification. Read-only.

select
    state,
    source_quality,
    group_code,
    count(*) as entitlement_count
from public.customer_entitlements_v2
group by state, source_quality, group_code
order by state, source_quality, group_code;

select count(*) as duplicate_entitlement_keys
from (
    select source_order_id, group_code
    from public.customer_entitlements_v2
    group by source_order_id, group_code
    having count(*) > 1
) duplicates;

select count(*) as invalid_timed_entitlements
from public.customer_entitlements_v2
where not is_lifetime
  and expires_at is null;

select count(*) as unsupported_kickable_entitlements
from public.customer_entitlements_v2
where source_quality = 'VERIFIED'
  and state in ('ACTIVE', 'EXPIRED')
  and group_code is null;

select count(*) as cancelled_entitlements
from public.customer_entitlements_v2
where state = 'CANCELLED';

select count(*) as review_entitlements
from public.customer_entitlements_v2
where state = 'REVIEW' or source_quality = 'REVIEW';
