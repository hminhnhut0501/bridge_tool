create table if not exists public.renewal_kick_tasks (
  id uuid primary key default gen_random_uuid(),
  order_id text not null,
  telegram_user_id text not null,
  group_id text not null,
  plan_name text not null,
  expire_at timestamptz,
  due_at timestamptz not null,
  state text not null default 'queued',
  attempt_count integer not null default 0,
  next_retry_at timestamptz,
  last_error text,
  last_error_code text,
  locked_by text,
  locked_at timestamptz,
  requested_at timestamptz,
  processing_at timestamptz,
  confirmed_at timestamptz,
  completed_at timestamptz,
  resolved_at timestamptz,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists idx_renewal_kick_tasks_unique on public.renewal_kick_tasks (order_id, group_id);
create index if not exists idx_renewal_kick_tasks_state_retry on public.renewal_kick_tasks (state, next_retry_at, due_at);
create index if not exists idx_renewal_kick_tasks_order_id on public.renewal_kick_tasks (order_id);
create index if not exists idx_renewal_kick_tasks_user_id on public.renewal_kick_tasks (telegram_user_id);

drop trigger if exists touch_renewal_kick_tasks_updated_at on public.renewal_kick_tasks;
create trigger touch_renewal_kick_tasks_updated_at
before update on public.renewal_kick_tasks
for each row execute function public.touch_updated_at();

alter table public.renewal_kick_tasks enable row level security;

drop policy if exists "service_role_full_access_renewal_kick_tasks" on public.renewal_kick_tasks;
create policy "service_role_full_access_renewal_kick_tasks"
on public.renewal_kick_tasks for all
to service_role
using (true)
with check (true);

notify pgrst, 'reload schema';
