create table if not exists public.renewal_admin_mutation_audit (
    id uuid primary key default gen_random_uuid(),
    action text not null,
    idempotency_key text not null unique,
    actor text not null,
    status text not null,
    payload jsonb not null default '{}'::jsonb,
    error text,
    created_at timestamptz not null default now()
);
create index if not exists renewal_admin_mutation_audit_action_idx
  on public.renewal_admin_mutation_audit (action, created_at desc);
