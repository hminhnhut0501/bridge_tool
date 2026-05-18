create or replace function public.touch_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

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

drop trigger if exists touch_security_blacklist_updated_at on public.security_blacklist;
create trigger touch_security_blacklist_updated_at
before update on public.security_blacklist
for each row execute function public.touch_updated_at();

alter table public.security_blacklist enable row level security;

drop policy if exists "service_role_full_access_security_blacklist" on public.security_blacklist;
create policy "service_role_full_access_security_blacklist"
on public.security_blacklist for all
to service_role
using (true)
with check (true);

notify pgrst, 'reload schema';
