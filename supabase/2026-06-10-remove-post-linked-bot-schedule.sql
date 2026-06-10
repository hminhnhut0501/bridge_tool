-- Remove the old channel-post-linked bot runtime mechanism.
-- Channel posts keep only repeat_daily; bot availability is controlled by bot_config.

drop index if exists public.idx_channel_posts_sync_schedule;
drop index if exists public.idx_bot_schedule_rules_status_window;
drop index if exists public.idx_bot_schedule_rules_channel_post_id;
drop index if exists public.idx_bot_schedule_rules_updated_at;

drop trigger if exists touch_bot_schedule_rules_updated_at on public.bot_schedule_rules;
drop table if exists public.bot_schedule_rules;
drop table if exists public.bot_runtime_state;

alter table public.channel_posts
  add column if not exists repeat_daily boolean not null default false;

alter table public.channel_posts
  drop column if exists sync_bot_schedule;

create index if not exists idx_channel_posts_repeat_schedule
on public.channel_posts (bot_key, repeat_daily, enabled, scheduled_at, delete_at);
