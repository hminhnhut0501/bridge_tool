create or replace function public.touch_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create table if not exists public.user_preferences (
  telegram_user_id text primary key,
  language text not null default 'vi',
  updated_at timestamptz not null default now()
);

drop trigger if exists touch_user_preferences_updated_at on public.user_preferences;
create trigger touch_user_preferences_updated_at
before update on public.user_preferences
for each row execute function public.touch_updated_at();

alter table public.user_preferences enable row level security;

drop policy if exists "service_role_full_access_user_preferences" on public.user_preferences;
create policy "service_role_full_access_user_preferences"
on public.user_preferences for all
to service_role
using (true)
with check (true);

create table if not exists public.security_blacklist (
  id uuid primary key default gen_random_uuid(),
  telegram_user_id text not null unique,
  username text,
  full_name text,
  reason text not null default '',
  source text not null default 'dashboard',
  is_active boolean not null default true,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_security_blacklist_telegram_user_id on public.security_blacklist (telegram_user_id);
create index if not exists idx_security_blacklist_is_active on public.security_blacklist (is_active);

drop trigger if exists touch_security_blacklist_updated_at on public.security_blacklist;
create trigger touch_security_blacklist_updated_at
before update on public.security_blacklist
for each row execute function public.touch_updated_at();

alter table public.security_blacklist enable row level security;

drop policy if exists "service_role_full_access_security_blacklist" on public.security_blacklist;
create policy "service_role_full_access_security_blacklist"
on public.security_blacklist for all
to service_role
using (true)
with check (true);

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

create table if not exists public.support_tickets (
  id uuid primary key default gen_random_uuid(),
  ticket_no text not null unique,
  telegram_user_id text not null unique,
  chat_id text,
  username text,
  full_name text,
  manager_chat_id text,
  manager_group_message_id bigint,
  manager_topic_thread_id bigint,
  manager_topic_name text,
  status text not null default 'open',
  subject text,
  source text not null default 'bot',
  last_message_at timestamptz,
  closed_at timestamptz,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.support_tickets
  add column if not exists manager_group_message_id bigint;

create index if not exists idx_support_tickets_status_updated_at on public.support_tickets (status, updated_at desc);
create index if not exists idx_support_tickets_telegram_user_id on public.support_tickets (telegram_user_id);
create index if not exists idx_support_tickets_manager_topic_thread_id on public.support_tickets (manager_topic_thread_id);
create index if not exists idx_support_tickets_created_at on public.support_tickets (created_at desc);

drop trigger if exists touch_support_tickets_updated_at on public.support_tickets;
create trigger touch_support_tickets_updated_at
before update on public.support_tickets
for each row execute function public.touch_updated_at();

create table if not exists public.support_messages (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid not null references public.support_tickets(id) on delete cascade,
  direction text not null,
  telegram_message_id bigint,
  manager_group_message_id bigint,
  manager_topic_message_id bigint,
  reply_to_manager_message_id bigint,
  text text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_support_messages_ticket_created_at on public.support_messages (ticket_id, created_at desc);
create index if not exists idx_support_messages_manager_group_message_id on public.support_messages (manager_group_message_id);
create index if not exists idx_support_messages_manager_topic_message_id on public.support_messages (manager_topic_message_id);

alter table public.support_tickets enable row level security;
alter table public.support_messages enable row level security;

drop policy if exists "service_role_full_access_support_tickets" on public.support_tickets;
create policy "service_role_full_access_support_tickets"
on public.support_tickets for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_support_messages" on public.support_messages;
create policy "service_role_full_access_support_messages"
on public.support_messages for all
to service_role
using (true)
with check (true);

notify pgrst, 'reload schema';
