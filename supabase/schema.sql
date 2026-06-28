create extension if not exists pgcrypto;

create table if not exists public.orders (
  id uuid primary key default gen_random_uuid(),
  order_id text not null unique,
  telegram_user_id text not null,
  full_name text,
  plan_name text not null,
  amount numeric(14,2) not null default 0,
  status text not null default 'PENDING',
  paid_at timestamptz,
  expire_at timestamptz,
  sale_id text,
  original_amount numeric(14,2),
  coupon_code text,
  coupon_discount_percent integer,
  coupon_discount_amount numeric(14,2),
  last_reminder_date date,
  expired_notice_at timestamptz,
  payment_message_chat_id text,
  payment_message_id integer,
  payment_provider text,
  payment_provider_order_id text,
  payment_approval_url text,
  payment_currency text not null default 'VND',
  note text,
  plan_token text,
  plan_category text,
  source_type text,
  source_ref text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.order_activation_codes (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  order_id text not null unique,
  telegram_user_id text not null,
  full_name text,
  plan_name text not null,
  expire_at timestamptz,
  activation_status text not null default 'PENDING',
  activated_at timestamptz,
  activated_by_user_id text,
  used_at timestamptz,
  used_by_user_id text,
  activation_url text,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_order_activation_codes_code on public.order_activation_codes (code);
create index if not exists idx_order_activation_codes_order_id on public.order_activation_codes (order_id);
create index if not exists idx_order_activation_codes_telegram_user_id on public.order_activation_codes (telegram_user_id);

create index if not exists idx_orders_telegram_user_id on public.orders (telegram_user_id);
create index if not exists idx_orders_status on public.orders (status);
create index if not exists idx_orders_expire_at on public.orders (expire_at);
create index if not exists idx_orders_plan_token on public.orders (plan_token);
create index if not exists idx_orders_plan_category on public.orders (plan_category);
create index if not exists idx_orders_source_type on public.orders (source_type);

create table if not exists public.bot_config (
  key text primary key,
  value text not null default '',
  updated_at timestamptz not null default now()
);

create table if not exists public.user_preferences (
  telegram_user_id text primary key,
  language text not null default 'vi',
  updated_at timestamptz not null default now()
);

create table if not exists public.menu_pages (
  page_id text primary key,
  image_url text,
  body text not null default '',
  layout text not null default '',
  updated_at timestamptz not null default now()
);

create table if not exists public.sale_rules (
  id uuid primary key default gen_random_uuid(),
  sale_id text unique,
  price_key text not null,
  discount_percent integer,
  sale_price numeric(14,2),
  starts_at timestamptz,
  ends_at timestamptz,
  slot_limit integer,
  used_count integer not null default 0,
  enabled boolean not null default true,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.coupons (
  id uuid primary key default gen_random_uuid(),
  code text not null unique,
  plan_name text,
  amount integer,
  status text not null default 'ACTIVE',
  max_uses integer,
  used_count integer not null default 0,
  expires_at timestamptz,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.coupon_redemptions (
  id uuid primary key default gen_random_uuid(),
  coupon_code text not null,
  telegram_user_id text not null,
  order_id text,
  redeemed_at timestamptz not null default now(),
  raw_data jsonb not null default '{}'::jsonb
);

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

create table if not exists public.analytics_events (
  id uuid primary key default gen_random_uuid(),
  event_name text not null,
  telegram_user_id text,
  payload jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

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

create table if not exists public.channel_post_events (
  id bigserial primary key,
  bot_key text not null default 'main',
  channel_post_id bigint references public.channel_posts(id) on delete cascade,
  event_type text not null,
  message text,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.hidden_groups (
  id text primary key,
  name text not null,
  description text not null default '',
  chat_id text not null,
  price_1m_vnd numeric(14,2) not null default 0,
  price_life_vnd numeric(14,2) not null default 0,
  price_1m_usd numeric(14,2) not null default 0,
  price_life_usd numeric(14,2) not null default 0,
  duration_1m_days integer not null default 30,
  lifetime_days integer not null default 3650,
  image_url text,
  requirement_type text not null default 'NONE',
  requirement_value text not null default '',
  sort_order integer not null default 0,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.hidden_codes (
  code text primary key,
  name text not null default '',
  description text not null default '',
  scope_type text not null default 'SELECTED_GROUPS',
  group_ids jsonb not null default '[]'::jsonb,
  requirement_type text,
  requirement_value text not null default '',
  max_uses integer not null default 0,
  used_count integer not null default 0,
  valid_from timestamptz,
  valid_until timestamptz,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.hidden_code_redemptions (
  id uuid primary key default gen_random_uuid(),
  code text not null references public.hidden_codes(code) on delete cascade,
  telegram_user_id text not null,
  full_name text not null default '',
  username text not null default '',
  revealed_group_ids jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_broadcast_campaigns_status on public.broadcast_campaigns (status);
create index if not exists idx_broadcast_campaigns_created_at on public.broadcast_campaigns (created_at desc);
create index if not exists idx_broadcast_recipients_campaign_id on public.broadcast_recipients (campaign_id);
create index if not exists idx_broadcast_recipients_status on public.broadcast_recipients (status);
create index if not exists idx_broadcast_recipients_user on public.broadcast_recipients (telegram_user_id);
create index if not exists idx_broadcast_events_campaign_id on public.broadcast_events (campaign_id);
create index if not exists idx_channel_posts_status_schedule on public.channel_posts (bot_key, status, scheduled_at);
create index if not exists idx_channel_posts_delete_schedule on public.channel_posts (bot_key, status, delete_at);
create index if not exists idx_channel_posts_repeat_schedule on public.channel_posts (bot_key, repeat_daily, enabled, scheduled_at, delete_at);
create index if not exists idx_channel_posts_updated_at on public.channel_posts (updated_at desc);
create index if not exists idx_channel_post_events_post on public.channel_post_events (channel_post_id, created_at desc);
create index if not exists idx_hidden_groups_active_order on public.hidden_groups (is_active, sort_order, name);
create index if not exists idx_hidden_groups_chat_id on public.hidden_groups (chat_id);
create index if not exists idx_hidden_codes_active on public.hidden_codes (is_active, code);
create index if not exists idx_hidden_codes_valid_until on public.hidden_codes (valid_until);
create index if not exists idx_hidden_code_redemptions_code_created on public.hidden_code_redemptions (code, created_at desc);
create index if not exists idx_hidden_code_redemptions_user_created on public.hidden_code_redemptions (telegram_user_id, created_at desc);

create or replace function public.touch_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists touch_orders_updated_at on public.orders;
create trigger touch_orders_updated_at
before update on public.orders
for each row execute function public.touch_updated_at();

drop trigger if exists touch_bot_config_updated_at on public.bot_config;
create trigger touch_bot_config_updated_at
before update on public.bot_config
for each row execute function public.touch_updated_at();

drop trigger if exists touch_user_preferences_updated_at on public.user_preferences;
create trigger touch_user_preferences_updated_at
before update on public.user_preferences
for each row execute function public.touch_updated_at();

drop trigger if exists touch_menu_pages_updated_at on public.menu_pages;
create trigger touch_menu_pages_updated_at
before update on public.menu_pages
for each row execute function public.touch_updated_at();

drop trigger if exists touch_sale_rules_updated_at on public.sale_rules;
create trigger touch_sale_rules_updated_at
before update on public.sale_rules
for each row execute function public.touch_updated_at();

drop trigger if exists touch_coupons_updated_at on public.coupons;
create trigger touch_coupons_updated_at
before update on public.coupons
for each row execute function public.touch_updated_at();

drop trigger if exists touch_security_blacklist_updated_at on public.security_blacklist;
create trigger touch_security_blacklist_updated_at
before update on public.security_blacklist
for each row execute function public.touch_updated_at();

drop trigger if exists touch_broadcast_campaigns_updated_at on public.broadcast_campaigns;
create trigger touch_broadcast_campaigns_updated_at
before update on public.broadcast_campaigns
for each row execute function public.touch_updated_at();

drop trigger if exists touch_broadcast_recipients_updated_at on public.broadcast_recipients;
create trigger touch_broadcast_recipients_updated_at
before update on public.broadcast_recipients
for each row execute function public.touch_updated_at();

drop trigger if exists touch_channel_posts_updated_at on public.channel_posts;
create trigger touch_channel_posts_updated_at
before update on public.channel_posts
for each row execute function public.touch_updated_at();

drop trigger if exists touch_hidden_groups_updated_at on public.hidden_groups;
create trigger touch_hidden_groups_updated_at
before update on public.hidden_groups
for each row execute function public.touch_updated_at();

drop trigger if exists touch_hidden_codes_updated_at on public.hidden_codes;
create trigger touch_hidden_codes_updated_at
before update on public.hidden_codes
for each row execute function public.touch_updated_at();

alter table public.orders enable row level security;
alter table public.bot_config enable row level security;
alter table public.user_preferences enable row level security;
alter table public.menu_pages enable row level security;
alter table public.sale_rules enable row level security;
alter table public.coupons enable row level security;
alter table public.coupon_redemptions enable row level security;
alter table public.security_blacklist enable row level security;
alter table public.support_events enable row level security;
alter table public.analytics_events enable row level security;
alter table public.broadcast_campaigns enable row level security;
alter table public.broadcast_recipients enable row level security;
alter table public.broadcast_events enable row level security;
alter table public.channel_posts enable row level security;
alter table public.channel_post_events enable row level security;
alter table public.hidden_groups enable row level security;
alter table public.hidden_codes enable row level security;
alter table public.hidden_code_redemptions enable row level security;

drop policy if exists "service_role_full_access_orders" on public.orders;
create policy "service_role_full_access_orders"
on public.orders for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_bot_config" on public.bot_config;
create policy "service_role_full_access_bot_config"
on public.bot_config for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_user_preferences" on public.user_preferences;
create policy "service_role_full_access_user_preferences"
on public.user_preferences for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_menu_pages" on public.menu_pages;
create policy "service_role_full_access_menu_pages"
on public.menu_pages for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_sale_rules" on public.sale_rules;
create policy "service_role_full_access_sale_rules"
on public.sale_rules for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_coupons" on public.coupons;
create policy "service_role_full_access_coupons"
on public.coupons for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_coupon_redemptions" on public.coupon_redemptions;
create policy "service_role_full_access_coupon_redemptions"
on public.coupon_redemptions for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_security_blacklist" on public.security_blacklist;
create policy "service_role_full_access_security_blacklist"
on public.security_blacklist for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_support_events" on public.support_events;
create policy "service_role_full_access_support_events"
on public.support_events for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_analytics_events" on public.analytics_events;
create policy "service_role_full_access_analytics_events"
on public.analytics_events for all
to service_role
using (true)
with check (true);

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

drop policy if exists "service_role_full_access_hidden_groups" on public.hidden_groups;
create policy "service_role_full_access_hidden_groups"
on public.hidden_groups for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_hidden_codes" on public.hidden_codes;
create policy "service_role_full_access_hidden_codes"
on public.hidden_codes for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_hidden_code_redemptions" on public.hidden_code_redemptions;
create policy "service_role_full_access_hidden_code_redemptions"
on public.hidden_code_redemptions for all
to service_role
using (true)
with check (true);
