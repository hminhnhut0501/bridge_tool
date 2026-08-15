-- Phase B: controlled backfill into the new entitlement contract.
-- Only canonical, non-cancelled rows are copied. No kick jobs are created.

begin;

insert into public.customer_entitlements_v2 (
    source_order_id,
    telegram_user_id,
    group_code,
    group_id,
    starts_at,
    expires_at,
    is_lifetime,
    state,
    source_quality
)
select
    o.order_id::text,
    o.telegram_user_id::text,
    o.canonical_group_code,
    null,
    coalesce(o.paid_at, o.created_at),
    o.expire_at,
    o.canonical_duration = 'LIFETIME',
    case
        when o.canonical_duration = 'LIFETIME' then 'ACTIVE'
        when upper(o.status) = 'PAID' and o.expire_at > now() then 'ACTIVE'
        else 'EXPIRED'
    end,
    'VERIFIED'
from public.orders o
where upper(o.status) in ('PAID', 'EXPIRED')
  and o.canonical_plan_family is not null
  and o.canonical_plan_family <> 'UNSUPPORTED'
  and o.canonical_duration is not null
  and o.canonical_duration <> 'REVIEW'
  and o.canonical_group_code is not null
  and (o.canonical_duration = 'LIFETIME' or o.expire_at is not null)
on conflict (source_order_id, group_code) do update
set telegram_user_id = excluded.telegram_user_id,
    starts_at = excluded.starts_at,
    expires_at = excluded.expires_at,
    is_lifetime = excluded.is_lifetime,
    state = excluded.state,
    source_quality = excluded.source_quality,
    updated_at = now();

commit;
