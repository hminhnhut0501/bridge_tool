-- Phase 2: read-only entitlement projection.
-- This view does not create kick tasks and does not mutate orders.

create or replace view public.customer_entitlements_v1 as
select
    o.order_id as source_order_id,
    o.telegram_user_id,
    o.canonical_plan_family as plan_family,
    o.canonical_group_code as group_code,
    o.paid_at as starts_at,
    o.expire_at as expires_at,
    (o.canonical_duration = 'LIFETIME') as is_lifetime,
    case
        when upper(coalesce(o.status, '')) = 'CANCELLED' then 'CANCELLED'
        when upper(coalesce(o.status, '')) = 'REFUNDED' then 'CANCELLED'
        when o.canonical_plan_family = 'UNSUPPORTED'
          or o.canonical_duration = 'REVIEW'
          or o.canonical_plan_family is null
          or o.canonical_group_code is null then 'REVIEW'
        when upper(coalesce(o.status, '')) = 'PAID'
          and o.canonical_duration = 'LIFETIME' then 'ACTIVE'
        when upper(coalesce(o.status, '')) = 'PAID'
          and o.expire_at > now() then 'ACTIVE'
        when upper(coalesce(o.status, '')) = 'EXPIRED'
          or (upper(coalesce(o.status, '')) = 'PAID' and o.expire_at <= now()) then 'EXPIRED'
        else 'REVIEW'
    end as state,
    case
        when upper(coalesce(o.status, '')) = 'CANCELLED' then 'order_cancelled'
        when upper(coalesce(o.status, '')) = 'REFUNDED' then 'order_refunded'
        when o.canonical_plan_family = 'UNSUPPORTED'
          or o.canonical_duration = 'REVIEW'
          or o.canonical_plan_family is null
          or o.canonical_group_code is null then 'canonical_mapping_incomplete'
        when upper(coalesce(o.status, '')) = 'PAID'
          and o.canonical_duration = 'LIFETIME' then 'lifetime_order'
        when upper(coalesce(o.status, '')) = 'PAID' and o.expire_at > now() then 'future_expiry'
        when upper(coalesce(o.status, '')) = 'EXPIRED'
          or (upper(coalesce(o.status, '')) = 'PAID' and o.expire_at <= now()) then 'expiry_reached'
        else 'unsupported_order_state'
    end as state_reason,
    case
        when o.canonical_plan_family is not null
         and o.canonical_group_code is not null
         and o.canonical_duration is not null then 'VERIFIED'
        else 'REVIEW'
    end as source_quality
from public.orders o;

comment on view public.customer_entitlements_v1 is
  'Read-only Phase 2 projection. Kick workers must not mutate or infer from this view.';
