-- Phase A: minimal entitlement contract for the rebuilt kick flow.
-- Schema only. No legacy order is copied automatically in this phase.

create table if not exists public.customer_entitlements_v2 (
    id uuid primary key default gen_random_uuid(),
    source_order_id text not null,
    telegram_user_id text not null,
    group_code text not null,
    group_id text,
    starts_at timestamptz,
    expires_at timestamptz,
    is_lifetime boolean not null default false,
    state text not null default 'ACTIVE',
    source_quality text not null default 'REVIEW',
    kick_job_created_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint customer_entitlements_v2_state_check
      check (state in ('ACTIVE', 'EXPIRED', 'CANCELLED', 'REVIEW')),
    constraint customer_entitlements_v2_quality_check
      check (source_quality in ('VERIFIED', 'DERIVED', 'LEGACY', 'REVIEW')),
    constraint customer_entitlements_v2_group_check
      check (group_code in ('COMBO_FULL', 'PRIME', 'BOY', 'REAL', 'ASIA', 'PINK_SPECIAL')),
    constraint customer_entitlements_v2_expiry_check
      check (is_lifetime or expires_at is not null)
);

create unique index if not exists customer_entitlements_v2_source_group_uq
  on public.customer_entitlements_v2 (source_order_id, group_code);

create index if not exists customer_entitlements_v2_lookup_idx
  on public.customer_entitlements_v2 (telegram_user_id, group_code, state, expires_at);

create index if not exists customer_entitlements_v2_due_idx
  on public.customer_entitlements_v2 (state, expires_at)
  where state = 'ACTIVE' and is_lifetime = false;

comment on table public.customer_entitlements_v2 is
  'Minimal entitlement source for the rebuilt expiry/kick flow; legacy orders are not read by the worker.';
