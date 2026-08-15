-- Phase 8: read-only membership and reminder models.
-- Population is performed by dedicated adapters, not by the admin UI.

create table if not exists public.renewal_membership_snapshots (
    id uuid primary key default gen_random_uuid(),
    telegram_user_id text not null,
    group_id text not null,
    membership_status text not null,
    source text not null default 'telegram_read',
    checked_at timestamptz not null default now(),
    last_error text,
    constraint renewal_membership_status_check
      check (membership_status in ('PRESENT', 'ABSENT', 'UNKNOWN')),
    unique (telegram_user_id, group_id)
);

create table if not exists public.renewal_reminder_events (
    id uuid primary key default gen_random_uuid(),
    order_id text not null,
    telegram_user_id text not null,
    reminder_type text not null,
    status text not null,
    sent_at timestamptz,
    attempts integer not null default 0,
    last_error text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    constraint renewal_reminder_status_check
      check (status in ('PENDING', 'SENT', 'FAILED'))
);

create index if not exists renewal_membership_snapshot_lookup
  on public.renewal_membership_snapshots (telegram_user_id, group_id, checked_at desc);
create index if not exists renewal_reminder_order_lookup
  on public.renewal_reminder_events (order_id, updated_at desc);
