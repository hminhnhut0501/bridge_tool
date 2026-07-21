create extension if not exists pgcrypto;

create or replace function public.touch_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create table if not exists public.bot_config (
  key text primary key,
  value text not null default '',
  updated_at timestamptz not null default now()
);

create table if not exists public.licenses (
  id uuid primary key default gen_random_uuid(),
  license_key text not null unique,
  order_id text not null unique,
  telegram_user_id text not null,
  full_name text,
  plan_code text not null,
  plan_slug text,
  status text not null default 'issued',
  expires_at timestamptz,
  is_lifetime boolean not null default false,
  source text not null default 'web',
  activated_at timestamptz,
  last_verified_at timestamptz,
  revoked_at timestamptz,
  group_ids jsonb not null default '[]'::jsonb,
  binding_state text not null default 'unbound',
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_licenses_license_key on public.licenses (license_key);
create index if not exists idx_licenses_order_id on public.licenses (order_id);
create index if not exists idx_licenses_telegram_user_id on public.licenses (telegram_user_id);
create index if not exists idx_licenses_status on public.licenses (status);

alter table public.licenses
  add column if not exists last_session_at timestamptz,
  add column if not exists renew_reminder_sent_at timestamptz,
  add column if not exists revoked_notice_sent_at timestamptz,
  add column if not exists lifecycle_metadata jsonb not null default '{}'::jsonb;

update public.licenses
set
  lifecycle_metadata = coalesce(lifecycle_metadata, '{}'::jsonb),
  updated_at = coalesce(updated_at, now())
where
  lifecycle_metadata is null
  or updated_at is null;

insert into public.bot_config (key, value, updated_at)
values
  (
    'LICENSE_PLAN_MAPPING_JSON',
    '{
      "VIP_BASIC":{"groups":["group_a"],"duration_days":30,"allow_renew":true},
      "VIP_PRO":{"groups":["group_a","group_b"],"duration_days":30,"allow_renew":true},
      "VIP_LIFE":{"groups":["group_a","group_b","group_c"],"duration_days":null,"allow_renew":false}
    }',
    now()
  ),
  (
    'MSG_LICENSE_REMINDER',
    '⏰ License <b>{plan}</b> của bạn sẽ hết hạn sau <b>{days} ngày</b> nữa.\n\nVui lòng gia hạn để giữ quyền truy cập không gián đoạn.',
    now()
  ),
  (
    'MSG_LICENSE_REVOKED',
    '⛔ License <b>{plan}</b> của bạn đã bị thu hồi. Vui lòng liên hệ hỗ trợ nếu cần kiểm tra lại.',
    now()
  ),
  (
    'BTN_LICENSE_RENEW',
    '🔄 Gia hạn license',
    now()
  )
on conflict (key) do update
set
  value = excluded.value,
  updated_at = now()
where public.bot_config.key in (
  'LICENSE_PLAN_MAPPING_JSON',
  'MSG_LICENSE_REMINDER',
  'MSG_LICENSE_REVOKED',
  'BTN_LICENSE_RENEW'
);

create table if not exists public.license_sessions (
  id uuid primary key default gen_random_uuid(),
  license_key text not null,
  telegram_user_id text not null,
  plan_code text,
  status text not null default 'pending',
  action text not null default 'verify',
  source text not null default 'web',
  request_payload jsonb not null default '{}'::jsonb,
  response_payload jsonb not null default '{}'::jsonb,
  raw_data jsonb not null default '{}'::jsonb,
  verified_at timestamptz,
  activated_at timestamptz,
  expires_at timestamptz,
  last_seen_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.license_session_events (
  id uuid primary key default gen_random_uuid(),
  license_key text not null,
  telegram_user_id text not null,
  plan_code text,
  status text,
  action text not null default 'event',
  source text not null default 'bot',
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.license_audit_events (
  id uuid primary key default gen_random_uuid(),
  license_key text not null,
  telegram_user_id text not null,
  event_type text not null,
  plan_code text,
  result text not null default '',
  source text not null default 'bot',
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_license_sessions_license_key on public.license_sessions (license_key);
create index if not exists idx_license_sessions_telegram_user_id on public.license_sessions (telegram_user_id);
create index if not exists idx_license_sessions_status on public.license_sessions (status);
create index if not exists idx_license_sessions_created_at on public.license_sessions (created_at desc);

create index if not exists idx_license_session_events_license_key on public.license_session_events (license_key);
create index if not exists idx_license_session_events_telegram_user_id on public.license_session_events (telegram_user_id);
create index if not exists idx_license_session_events_created_at on public.license_session_events (created_at desc);

create index if not exists idx_license_audit_events_license_key on public.license_audit_events (license_key);
create index if not exists idx_license_audit_events_event_type on public.license_audit_events (event_type);
create index if not exists idx_license_audit_events_telegram_user_id on public.license_audit_events (telegram_user_id);
create index if not exists idx_license_audit_events_created_at on public.license_audit_events (created_at desc);

drop trigger if exists touch_license_sessions_updated_at on public.license_sessions;
create trigger touch_license_sessions_updated_at
before update on public.license_sessions
for each row execute function public.touch_updated_at();

alter table public.licenses enable row level security;
alter table public.license_sessions enable row level security;
alter table public.license_session_events enable row level security;
alter table public.license_audit_events enable row level security;

drop policy if exists "service_role_full_access_licenses" on public.licenses;
create policy "service_role_full_access_licenses"
on public.licenses for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_license_sessions" on public.license_sessions;
create policy "service_role_full_access_license_sessions"
on public.license_sessions for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_license_session_events" on public.license_session_events;
create policy "service_role_full_access_license_session_events"
on public.license_session_events for all
to service_role
using (true)
with check (true);

drop policy if exists "service_role_full_access_license_audit_events" on public.license_audit_events;
create policy "service_role_full_access_license_audit_events"
on public.license_audit_events for all
to service_role
using (true)
with check (true);

notify pgrst, 'reload schema';
