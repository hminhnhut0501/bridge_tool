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
