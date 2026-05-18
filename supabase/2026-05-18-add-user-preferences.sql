create or replace function public.touch_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create table if not exists public.user_preferences (
  telegram_user_id text primary key,
  language text not null default 'vi',
  updated_at timestamptz not null default now()
);

drop trigger if exists touch_user_preferences_updated_at on public.user_preferences;
create trigger touch_user_preferences_updated_at
before update on public.user_preferences
for each row execute function public.touch_updated_at();

alter table public.user_preferences enable row level security;

drop policy if exists "service_role_full_access_user_preferences" on public.user_preferences;
create policy "service_role_full_access_user_preferences"
on public.user_preferences for all
to service_role
using (true)
with check (true);

notify pgrst, 'reload schema';
