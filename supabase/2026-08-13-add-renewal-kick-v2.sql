create extension if not exists pgcrypto;

create table if not exists public.renewal_kick_tasks_v2 (
  id uuid primary key default gen_random_uuid(),
  order_id text not null,
  telegram_user_id text not null,
  plan_name text not null,

  task_state text not null default 'queued',
  priority integer not null default 0,
  due_at timestamptz not null,
  locked_at timestamptz,
  locked_by text,
  last_transition_at timestamptz not null default now(),

  total_groups integer not null default 0,
  kicked_groups integer not null default 0,
  retained_groups integer not null default 0,
  pending_groups integer not null default 0,
  error_groups integer not null default 0,
  review_groups integer not null default 0,

  attempt_count integer not null default 0,
  confirm_count integer not null default 0,
  retry_count integer not null default 0,

  last_error text,
  last_reason text,
  review_reason text,
  terminal_reason text,

  metadata jsonb not null default '{}'::jsonb,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz,
  resolved_at timestamptz
);

create unique index if not exists idx_renewal_kick_tasks_v2_unique
  on public.renewal_kick_tasks_v2 (order_id, telegram_user_id);

create index if not exists idx_renewal_kick_tasks_v2_state_due
  on public.renewal_kick_tasks_v2 (task_state, due_at, priority);

create index if not exists idx_renewal_kick_tasks_v2_user_order
  on public.renewal_kick_tasks_v2 (telegram_user_id, order_id);

create table if not exists public.renewal_kick_group_tasks_v2 (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references public.renewal_kick_tasks_v2(id) on delete cascade,

  order_id text not null,
  telegram_user_id text not null,
  group_id text not null,
  group_name text not null,
  group_no text,
  plan_name text not null,

  group_state text not null default 'pending',
  attempt_count integer not null default 0,
  confirm_count integer not null default 0,

  locked_at timestamptz,
  locked_by text,
  first_due_at timestamptz,
  next_retry_at timestamptz,
  last_transition_at timestamptz not null default now(),

  last_error text,
  last_reason text,
  review_reason text,
  terminal_reason text,

  metadata jsonb not null default '{}'::jsonb,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  completed_at timestamptz,
  resolved_at timestamptz
);

create unique index if not exists idx_renewal_kick_group_tasks_v2_unique
  on public.renewal_kick_group_tasks_v2 (task_id, group_id);

create index if not exists idx_renewal_kick_group_tasks_v2_state_retry
  on public.renewal_kick_group_tasks_v2 (group_state, next_retry_at);

create index if not exists idx_renewal_kick_group_tasks_v2_user_order
  on public.renewal_kick_group_tasks_v2 (telegram_user_id, order_id);

create index if not exists idx_renewal_kick_group_tasks_v2_task_id
  on public.renewal_kick_group_tasks_v2 (task_id);

create table if not exists public.renewal_kick_attempts_v2 (
  id uuid primary key default gen_random_uuid(),
  task_id uuid not null references public.renewal_kick_tasks_v2(id) on delete cascade,
  group_task_id uuid references public.renewal_kick_group_tasks_v2(id) on delete cascade,

  order_id text not null,
  telegram_user_id text not null,
  group_id text not null,
  group_name text not null,

  attempt_no integer not null,
  attempt_state text not null,
  action text not null,
  actor text not null,

  reason_code text,
  error_code text,
  error_message text,

  started_at timestamptz not null default now(),
  finished_at timestamptz,
  metadata jsonb not null default '{}'::jsonb
);

create index if not exists idx_renewal_kick_attempts_v2_task_group
  on public.renewal_kick_attempts_v2 (task_id, group_id, attempt_no);

create index if not exists idx_renewal_kick_attempts_v2_order_user
  on public.renewal_kick_attempts_v2 (order_id, telegram_user_id);

create index if not exists idx_renewal_kick_attempts_v2_group_state
  on public.renewal_kick_attempts_v2 (group_id, attempt_state);

create table if not exists public.renewal_kick_legacy_map_v2 (
  id uuid primary key default gen_random_uuid(),
  legacy_key text not null unique,
  task_id uuid references public.renewal_kick_tasks_v2(id) on delete set null,
  group_task_id uuid references public.renewal_kick_group_tasks_v2(id) on delete set null,
  legacy_source text not null,
  legacy_ref text,
  migrated_at timestamptz not null default now(),
  metadata jsonb not null default '{}'::jsonb
);

create or replace function public.touch_renewal_kick_tasks_v2_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create or replace function public.touch_renewal_kick_group_tasks_v2_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_touch_renewal_kick_tasks_v2_updated_at on public.renewal_kick_tasks_v2;
create trigger trg_touch_renewal_kick_tasks_v2_updated_at
before update on public.renewal_kick_tasks_v2
for each row execute function public.touch_renewal_kick_tasks_v2_updated_at();

drop trigger if exists trg_touch_renewal_kick_group_tasks_v2_updated_at on public.renewal_kick_group_tasks_v2;
create trigger trg_touch_renewal_kick_group_tasks_v2_updated_at
before update on public.renewal_kick_group_tasks_v2
for each row execute function public.touch_renewal_kick_group_tasks_v2_updated_at();

alter table public.renewal_kick_tasks_v2 enable row level security;
alter table public.renewal_kick_group_tasks_v2 enable row level security;
alter table public.renewal_kick_attempts_v2 enable row level security;
alter table public.renewal_kick_legacy_map_v2 enable row level security;

drop policy if exists "service_role_full_access_renewal_kick_tasks_v2" on public.renewal_kick_tasks_v2;
create policy "service_role_full_access_renewal_kick_tasks_v2"
on public.renewal_kick_tasks_v2 for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_renewal_kick_group_tasks_v2" on public.renewal_kick_group_tasks_v2;
create policy "service_role_full_access_renewal_kick_group_tasks_v2"
on public.renewal_kick_group_tasks_v2 for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_renewal_kick_attempts_v2" on public.renewal_kick_attempts_v2;
create policy "service_role_full_access_renewal_kick_attempts_v2"
on public.renewal_kick_attempts_v2 for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_renewal_kick_legacy_map_v2" on public.renewal_kick_legacy_map_v2;
create policy "service_role_full_access_renewal_kick_legacy_map_v2"
on public.renewal_kick_legacy_map_v2 for all
to service_role
using (true)
with check (true);

comment on table public.renewal_kick_tasks_v2 is 'Parent renewal kick task, source of truth for renewal kick v2.';
comment on table public.renewal_kick_group_tasks_v2 is 'One row per group inside a renewal kick task.';
comment on table public.renewal_kick_attempts_v2 is 'Attempt-level audit trail for renewal kick v2.';
comment on table public.renewal_kick_legacy_map_v2 is 'Legacy support-events/task mapping during migration.';

notify pgrst, 'reload schema';
