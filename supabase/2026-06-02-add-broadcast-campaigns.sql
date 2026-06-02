create table if not exists public.broadcast_campaigns (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  message text not null default '',
  parse_mode text not null default 'HTML',
  target_segment text not null default 'ALL',
  status text not null default 'DRAFT',
  delay_seconds integer not null default 5,
  batch_size integer not null default 20,
  total_recipients integer not null default 0,
  sent_count integer not null default 0,
  failed_count integer not null default 0,
  skipped_count integer not null default 0,
  started_at timestamptz,
  finished_at timestamptz,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.broadcast_recipients (
  id uuid primary key default gen_random_uuid(),
  campaign_id uuid not null references public.broadcast_campaigns(id) on delete cascade,
  telegram_user_id text not null,
  username text,
  full_name text,
  segment text not null default '',
  status text not null default 'PENDING',
  attempt_count integer not null default 0,
  last_attempt_at timestamptz,
  sent_at timestamptz,
  error text,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (campaign_id, telegram_user_id)
);

create table if not exists public.broadcast_events (
  id uuid primary key default gen_random_uuid(),
  campaign_id uuid references public.broadcast_campaigns(id) on delete cascade,
  telegram_user_id text,
  event_type text not null,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_broadcast_campaigns_status on public.broadcast_campaigns (status);
create index if not exists idx_broadcast_campaigns_created_at on public.broadcast_campaigns (created_at desc);
create index if not exists idx_broadcast_recipients_campaign_id on public.broadcast_recipients (campaign_id);
create index if not exists idx_broadcast_recipients_status on public.broadcast_recipients (status);
create index if not exists idx_broadcast_recipients_user on public.broadcast_recipients (telegram_user_id);
create index if not exists idx_broadcast_events_campaign_id on public.broadcast_events (campaign_id);

drop trigger if exists touch_broadcast_campaigns_updated_at on public.broadcast_campaigns;
create trigger touch_broadcast_campaigns_updated_at
before update on public.broadcast_campaigns
for each row execute function public.touch_updated_at();

drop trigger if exists touch_broadcast_recipients_updated_at on public.broadcast_recipients;
create trigger touch_broadcast_recipients_updated_at
before update on public.broadcast_recipients
for each row execute function public.touch_updated_at();

alter table public.broadcast_campaigns enable row level security;
alter table public.broadcast_recipients enable row level security;
alter table public.broadcast_events enable row level security;

drop policy if exists "service_role_full_access_broadcast_campaigns" on public.broadcast_campaigns;
create policy "service_role_full_access_broadcast_campaigns"
on public.broadcast_campaigns for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_broadcast_recipients" on public.broadcast_recipients;
create policy "service_role_full_access_broadcast_recipients"
on public.broadcast_recipients for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_broadcast_events" on public.broadcast_events;
create policy "service_role_full_access_broadcast_events"
on public.broadcast_events for all
to service_role
using (true)
with check (true);
