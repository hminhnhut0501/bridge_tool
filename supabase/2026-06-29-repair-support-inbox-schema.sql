create extension if not exists pgcrypto;

create or replace function public.touch_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

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
  add column if not exists id uuid default gen_random_uuid(),
  add column if not exists ticket_no text,
  add column if not exists telegram_user_id text,
  add column if not exists chat_id text,
  add column if not exists username text,
  add column if not exists full_name text,
  add column if not exists manager_chat_id text,
  add column if not exists manager_group_message_id bigint,
  add column if not exists manager_topic_thread_id bigint,
  add column if not exists manager_topic_name text,
  add column if not exists status text default 'open',
  add column if not exists subject text,
  add column if not exists source text default 'bot',
  add column if not exists last_message_at timestamptz,
  add column if not exists closed_at timestamptz,
  add column if not exists raw_data jsonb default '{}'::jsonb,
  add column if not exists created_at timestamptz default now(),
  add column if not exists updated_at timestamptz default now();

update public.support_tickets
set
  id = coalesce(id, gen_random_uuid()),
  status = coalesce(nullif(status, ''), 'open'),
  source = coalesce(nullif(source, ''), 'bot'),
  raw_data = coalesce(raw_data, '{}'::jsonb),
  created_at = coalesce(created_at, now()),
  updated_at = coalesce(updated_at, created_at, now()),
  last_message_at = coalesce(last_message_at, updated_at, created_at)
where
  id is null
  or status is null
  or source is null
  or raw_data is null
  or created_at is null
  or updated_at is null
  or last_message_at is null;

alter table public.support_tickets
  alter column id set default gen_random_uuid(),
  alter column raw_data set default '{}'::jsonb,
  alter column created_at set default now(),
  alter column updated_at set default now();

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conrelid = 'public.support_tickets'::regclass
      and contype = 'p'
  ) then
    execute 'alter table public.support_tickets add constraint support_tickets_pkey primary key (id)';
  end if;
exception
  when duplicate_table then null;
  when duplicate_object then null;
end $$;

create unique index if not exists idx_support_tickets_id_unique
  on public.support_tickets (id);
create unique index if not exists idx_support_tickets_ticket_no_unique
  on public.support_tickets (ticket_no)
  where ticket_no is not null;
create unique index if not exists idx_support_tickets_telegram_user_id_unique
  on public.support_tickets (telegram_user_id)
  where telegram_user_id is not null;

create index if not exists idx_support_tickets_status_updated_at
  on public.support_tickets (status, updated_at desc);
create index if not exists idx_support_tickets_telegram_user_id
  on public.support_tickets (telegram_user_id);
create index if not exists idx_support_tickets_manager_topic_thread_id
  on public.support_tickets (manager_topic_thread_id);
create index if not exists idx_support_tickets_created_at
  on public.support_tickets (created_at desc);

drop trigger if exists touch_support_tickets_updated_at on public.support_tickets;
create trigger touch_support_tickets_updated_at
before update on public.support_tickets
for each row execute function public.touch_updated_at();

create table if not exists public.support_messages (
  id uuid primary key default gen_random_uuid(),
  ticket_id uuid not null,
  direction text not null,
  telegram_message_id bigint,
  manager_group_message_id bigint,
  manager_topic_message_id bigint,
  reply_to_manager_message_id bigint,
  text text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

alter table public.support_messages
  add column if not exists id uuid default gen_random_uuid(),
  add column if not exists ticket_id uuid,
  add column if not exists direction text,
  add column if not exists telegram_message_id bigint,
  add column if not exists manager_group_message_id bigint,
  add column if not exists manager_topic_message_id bigint,
  add column if not exists reply_to_manager_message_id bigint,
  add column if not exists text text,
  add column if not exists payload jsonb default '{}'::jsonb,
  add column if not exists created_at timestamptz default now();

update public.support_messages
set
  id = coalesce(id, gen_random_uuid()),
  payload = coalesce(payload, '{}'::jsonb),
  created_at = coalesce(created_at, now())
where
  id is null
  or payload is null
  or created_at is null;

alter table public.support_messages
  alter column id set default gen_random_uuid(),
  alter column payload set default '{}'::jsonb,
  alter column created_at set default now();

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conrelid = 'public.support_messages'::regclass
      and contype = 'p'
  ) then
    execute 'alter table public.support_messages add constraint support_messages_pkey primary key (id)';
  end if;
exception
  when duplicate_table then null;
  when duplicate_object then null;
end $$;

create unique index if not exists idx_support_messages_id_unique
  on public.support_messages (id);
create index if not exists idx_support_messages_ticket_created_at
  on public.support_messages (ticket_id, created_at desc);
create index if not exists idx_support_messages_manager_group_message_id
  on public.support_messages (manager_group_message_id);
create index if not exists idx_support_messages_manager_topic_message_id
  on public.support_messages (manager_topic_message_id);

do $$
begin
  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'support_messages'
      and column_name = 'ticket_id'
  ) and not exists (
    select 1
    from pg_constraint
    where conrelid = 'public.support_messages'::regclass
      and conname = 'support_messages_ticket_id_fkey'
  ) then
    execute 'alter table public.support_messages add constraint support_messages_ticket_id_fkey foreign key (ticket_id) references public.support_tickets(id) on delete cascade not valid';
  end if;
exception
  when duplicate_object then null;
end $$;

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
