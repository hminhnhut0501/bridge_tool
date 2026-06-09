alter table public.channel_posts
  add column if not exists repeat_daily boolean not null default false,
  add column if not exists sync_bot_schedule boolean not null default false;

create table if not exists public.bot_runtime_state (
  id text primary key default 'main',
  effective_mode text not null default 'always',
  source text not null default 'always',
  active boolean not null default true,
  title text not null default '',
  "window" text not null default '',
  detail text not null default '',
  timezone text not null default 'Asia/Ho_Chi_Minh',
  linked_count integer not null default 0,
  maintenance_mode boolean not null default false,
  maintenance_override boolean not null default false,
  fixed_schedule_enabled boolean not null default false,
  active_hours text not null default '',
  source_post_id text,
  source_post_title text,
  window_start timestamptz,
  window_end timestamptz,
  raw_data jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

drop trigger if exists touch_bot_runtime_state_updated_at on public.bot_runtime_state;
create trigger touch_bot_runtime_state_updated_at
before update on public.bot_runtime_state
for each row execute function public.touch_updated_at();

alter table public.bot_runtime_state enable row level security;

drop policy if exists "service_role_full_access_bot_runtime_state" on public.bot_runtime_state;
create policy "service_role_full_access_bot_runtime_state"
on public.bot_runtime_state for all
to service_role
using (true)
with check (true);

create table if not exists public.bot_schedule_rules (
  id bigserial primary key,
  bot_key text not null default 'main',
  channel_post_id bigint not null references public.channel_posts(id) on delete cascade,
  enabled boolean not null default true,
  repeat_daily boolean not null default false,
  sync_bot_schedule boolean not null default false,
  active_from timestamptz not null,
  active_to timestamptz not null,
  timezone text not null default 'Asia/Ho_Chi_Minh',
  source_post_title text not null default '',
  source_post_status text not null default '',
  source_post_target_chat_id text not null default '',
  notes text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(channel_post_id)
);

create index if not exists idx_bot_schedule_rules_status_window on public.bot_schedule_rules (bot_key, enabled, repeat_daily, sync_bot_schedule, active_from, active_to);
create index if not exists idx_bot_schedule_rules_channel_post_id on public.bot_schedule_rules (channel_post_id);
create index if not exists idx_bot_schedule_rules_updated_at on public.bot_schedule_rules (updated_at desc);

drop trigger if exists touch_bot_schedule_rules_updated_at on public.bot_schedule_rules;
create trigger touch_bot_schedule_rules_updated_at
before update on public.bot_schedule_rules
for each row execute function public.touch_updated_at();

alter table public.bot_schedule_rules enable row level security;

drop policy if exists "service_role_full_access_bot_schedule_rules" on public.bot_schedule_rules;
create policy "service_role_full_access_bot_schedule_rules"
on public.bot_schedule_rules for all
to service_role
using (true)
with check (true);

insert into public.bot_schedule_rules (
  bot_key,
  channel_post_id,
  enabled,
  repeat_daily,
  sync_bot_schedule,
  active_from,
  active_to,
  timezone,
  source_post_title,
  source_post_status,
  source_post_target_chat_id,
  notes
)
select
  coalesce(cp.bot_key, 'main'),
  cp.id,
  coalesce(cp.enabled, true),
  coalesce(cp.repeat_daily, false),
  coalesce(cp.sync_bot_schedule, false),
  cp.scheduled_at,
  cp.delete_at,
  'Asia/Ho_Chi_Minh',
  coalesce(cp.title, ''),
  coalesce(cp.status, ''),
  coalesce(cp.target_chat_id, ''),
  cp.notes
from public.channel_posts as cp
where coalesce(cp.enabled, true)
  and coalesce(cp.repeat_daily, false)
  and coalesce(cp.sync_bot_schedule, false)
  and cp.scheduled_at is not null
  and cp.delete_at is not null
on conflict (channel_post_id) do update set
  bot_key = excluded.bot_key,
  enabled = excluded.enabled,
  repeat_daily = excluded.repeat_daily,
  sync_bot_schedule = excluded.sync_bot_schedule,
  active_from = excluded.active_from,
  active_to = excluded.active_to,
  timezone = excluded.timezone,
  source_post_title = excluded.source_post_title,
  source_post_status = excluded.source_post_status,
  source_post_target_chat_id = excluded.source_post_target_chat_id,
  notes = excluded.notes,
  updated_at = now();
