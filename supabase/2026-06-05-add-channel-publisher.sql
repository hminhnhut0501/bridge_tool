create table if not exists public.channel_posts (
  id bigserial primary key,
  bot_key text not null default 'main',
  target_chat_id text not null,
  title text,
  image_ref text,
  content text not null,
  buttons_text text,
  parse_mode text not null default 'HTML',
  disable_web_page_preview boolean not null default false,
  status text not null default 'draft',
  sent_message_id text,
  sent_at timestamptz,
  scheduled_at timestamptz,
  delete_at timestamptz,
  deleted_at timestamptz,
  error text,
  error_code text,
  enabled boolean not null default true,
  repeat_daily boolean not null default false,
  notes text,
  attempt_count integer not null default 0,
  last_attempt_at timestamptz,
  created_by text,
  deleted_by text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

alter table public.channel_posts
  add column if not exists image_ref text,
  add column if not exists repeat_daily boolean not null default false;

create table if not exists public.channel_post_events (
  id bigserial primary key,
  bot_key text not null default 'main',
  channel_post_id bigint references public.channel_posts(id) on delete cascade,
  event_type text not null,
  message text,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_channel_posts_status_schedule on public.channel_posts (bot_key, status, scheduled_at);
create index if not exists idx_channel_posts_delete_schedule on public.channel_posts (bot_key, status, delete_at);
create index if not exists idx_channel_posts_repeat_schedule on public.channel_posts (bot_key, repeat_daily, enabled, scheduled_at, delete_at);
create index if not exists idx_channel_posts_updated_at on public.channel_posts (updated_at desc);
create index if not exists idx_channel_post_events_post on public.channel_post_events (channel_post_id, created_at desc);

drop trigger if exists touch_channel_posts_updated_at on public.channel_posts;
create trigger touch_channel_posts_updated_at
before update on public.channel_posts
for each row execute function public.touch_updated_at();

alter table public.channel_posts enable row level security;
alter table public.channel_post_events enable row level security;

drop policy if exists "service_role_full_access_channel_posts" on public.channel_posts;
create policy "service_role_full_access_channel_posts"
on public.channel_posts for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_channel_post_events" on public.channel_post_events;
create policy "service_role_full_access_channel_post_events"
on public.channel_post_events for all
to service_role
using (true)
with check (true);
