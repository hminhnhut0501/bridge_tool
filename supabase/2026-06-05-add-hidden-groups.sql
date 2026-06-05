alter table public.orders
add column if not exists plan_token text,
add column if not exists plan_category text,
add column if not exists source_type text,
add column if not exists source_ref text,
add column if not exists metadata jsonb not null default '{}'::jsonb;

create index if not exists idx_orders_plan_token on public.orders (plan_token);
create index if not exists idx_orders_plan_category on public.orders (plan_category);
create index if not exists idx_orders_source_type on public.orders (source_type);

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

create index if not exists idx_hidden_groups_active_order on public.hidden_groups (is_active, sort_order, name);
create index if not exists idx_hidden_groups_chat_id on public.hidden_groups (chat_id);

drop trigger if exists touch_hidden_groups_updated_at on public.hidden_groups;
create trigger touch_hidden_groups_updated_at
before update on public.hidden_groups
for each row execute function public.touch_updated_at();

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

create index if not exists idx_hidden_codes_active on public.hidden_codes (is_active, code);
create index if not exists idx_hidden_codes_valid_until on public.hidden_codes (valid_until);

drop trigger if exists touch_hidden_codes_updated_at on public.hidden_codes;
create trigger touch_hidden_codes_updated_at
before update on public.hidden_codes
for each row execute function public.touch_updated_at();

create table if not exists public.hidden_code_redemptions (
  id uuid primary key default gen_random_uuid(),
  code text not null references public.hidden_codes(code) on delete cascade,
  telegram_user_id text not null,
  full_name text not null default '',
  username text not null default '',
  revealed_group_ids jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_hidden_code_redemptions_code_created on public.hidden_code_redemptions (code, created_at desc);
create index if not exists idx_hidden_code_redemptions_user_created on public.hidden_code_redemptions (telegram_user_id, created_at desc);

alter table public.hidden_groups enable row level security;
alter table public.hidden_codes enable row level security;
alter table public.hidden_code_redemptions enable row level security;

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

notify pgrst, 'reload schema';
