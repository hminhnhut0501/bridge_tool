create extension if not exists pgcrypto;

create table if not exists public.orders (
  id uuid primary key default gen_random_uuid(),
  order_id text not null unique,
  telegram_user_id text not null,
  full_name text,
  plan_name text not null,
  amount integer not null default 0,
  status text not null default 'PENDING',
  paid_at timestamptz,
  expire_at timestamptz,
  sale_id text,
  original_amount integer,
  coupon_code text,
  coupon_discount_percent integer,
  coupon_discount_amount integer,
  last_reminder_date date,
  expired_notice_at timestamptz,
  payment_message_chat_id text,
  payment_message_id integer,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_orders_telegram_user_id on public.orders (telegram_user_id);
create index if not exists idx_orders_status on public.orders (status);
create index if not exists idx_orders_expire_at on public.orders (expire_at);

create table if not exists public.bot_config (
  key text primary key,
  value text not null default '',
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
  sale_price integer,
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

alter table public.orders enable row level security;
alter table public.bot_config enable row level security;
alter table public.menu_pages enable row level security;
alter table public.sale_rules enable row level security;
alter table public.coupons enable row level security;
alter table public.coupon_redemptions enable row level security;
alter table public.security_blacklist enable row level security;
alter table public.support_events enable row level security;
alter table public.analytics_events enable row level security;

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
