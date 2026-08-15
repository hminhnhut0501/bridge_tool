create table if not exists public.renewal_worker_config (
    worker_name text primary key,
    enabled boolean not null default false,
    interval_seconds integer not null default 300 check (interval_seconds >= 300),
    batch_limit integer not null default 5 check (batch_limit between 1 and 5),
    halted boolean not null default false,
    halt_reason text,
    last_run_at timestamptz,
    last_batch jsonb not null default '{}'::jsonb,
    updated_by text,
    updated_at timestamptz not null default now()
);
insert into public.renewal_worker_config (worker_name)
values ('entitlement_kick')
on conflict (worker_name) do nothing;

create table if not exists public.renewal_worker_config_audit (
    id uuid primary key default gen_random_uuid(),
    worker_name text not null,
    action text not null,
    payload jsonb not null default '{}'::jsonb,
    actor text not null,
    created_at timestamptz not null default now()
);
