-- Phase C: expand COMBO_FULL into one entitlement per target group.
-- Parent COMBO_FULL rows remain for audit; only child rows are kickable.

begin;

-- Keep this migration safe to run independently of the previous Phase C file.
create table if not exists public.entitlement_kick_jobs (
    id uuid primary key default gen_random_uuid(),
    entitlement_id uuid not null references public.customer_entitlements_v2(id),
    source_order_id text not null,
    telegram_user_id text not null,
    group_code text not null,
    group_id text not null,
    run_at timestamptz not null,
    status text not null default 'PENDING',
    attempts integer not null default 0,
    last_error text,
    locked_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint entitlement_kick_jobs_status_check
      check (status in ('PENDING', 'PROCESSING', 'DONE', 'RETAINED', 'SKIPPED', 'RETRY', 'REVIEW'))
);

create unique index if not exists entitlement_kick_jobs_entitlement_uq
  on public.entitlement_kick_jobs (entitlement_id);

create index if not exists entitlement_kick_jobs_due_idx
  on public.entitlement_kick_jobs (status, run_at)
  where status in ('PENDING', 'RETRY');

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
    e.source_order_id,
    e.telegram_user_id,
    case m.group_name
        when 'Prime' then 'PRIME'
        when 'Boy' then 'BOY'
        when 'Real' then 'REAL'
        when 'Asia' then 'ASIA'
    end,
    m.telegram_group_id,
    e.starts_at,
    e.expires_at,
    e.is_lifetime,
    e.state,
    e.source_quality
from public.customer_entitlements_v2 e
join public.canonical_group_map m
  on m.group_code = 'COMBO_FULL'
 and m.is_active = true
where e.group_code = 'COMBO_FULL'
  and e.source_quality = 'VERIFIED'
on conflict (source_order_id, group_code) do update
set group_id = excluded.group_id,
    starts_at = excluded.starts_at,
    expires_at = excluded.expires_at,
    is_lifetime = excluded.is_lifetime,
    state = excluded.state,
    source_quality = excluded.source_quality,
    updated_at = now();

-- Create delayed jobs only for complete child entitlements.
insert into public.entitlement_kick_jobs (
    entitlement_id, source_order_id, telegram_user_id, group_code, group_id, run_at
)
select
    e.id, e.source_order_id, e.telegram_user_id, e.group_code, e.group_id, e.expires_at
from public.customer_entitlements_v2 e
where e.source_quality = 'VERIFIED'
  and e.state in ('ACTIVE', 'EXPIRED')
  and e.is_lifetime = false
  and e.expires_at is not null
  and e.group_id is not null
  and e.group_code <> 'COMBO_FULL'
on conflict (entitlement_id) do nothing;

commit;
