create table if not exists public.support_events (
  id uuid primary key default gen_random_uuid(),
  event_type text not null,
  telegram_user_id text,
  username text,
  full_name text,
  chat_id text,
  chat_title text,
  order_id text,
  plan_name text,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_support_events_event_type on public.support_events (event_type);
create index if not exists idx_support_events_created_at on public.support_events (created_at desc);
create index if not exists idx_support_events_telegram_user_id on public.support_events (telegram_user_id);

alter table public.support_events enable row level security;

drop policy if exists "service_role_full_access_support_events" on public.support_events;
create policy "service_role_full_access_support_events"
on public.support_events for all
to service_role
using (true)
with check (true);

notify pgrst, 'reload schema';
