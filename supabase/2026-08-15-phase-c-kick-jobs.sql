-- Phase C: minimal delayed kick jobs.
-- This creates schedules only; it does not call Telegram.

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

-- Only complete, verified, timed entitlements with a known group are eligible.
-- Existing rows with group_id null intentionally produce no job.
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
on conflict (entitlement_id) do nothing;
