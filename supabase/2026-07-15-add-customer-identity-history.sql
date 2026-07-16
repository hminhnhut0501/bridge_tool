create table if not exists public.customer_identity_history (
  id uuid primary key default gen_random_uuid(),
  telegram_user_id text not null,
  username text,
  full_name text,
  previous_username text,
  previous_full_name text,
  changed_fields jsonb not null default '[]'::jsonb,
  source_event_type text not null default '',
  source_order_id text not null default '',
  source_chat_id text not null default '',
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_customer_identity_history_telegram_user_id on public.customer_identity_history (telegram_user_id);
create index if not exists idx_customer_identity_history_created_at on public.customer_identity_history (created_at desc);

alter table public.customer_identity_history enable row level security;

drop policy if exists "service_role_full_access_customer_identity_history" on public.customer_identity_history;
create policy "service_role_full_access_customer_identity_history"
on public.customer_identity_history for all
to service_role
using (true)
with check (true);
