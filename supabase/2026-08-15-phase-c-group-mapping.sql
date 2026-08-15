-- Phase C: canonical group mapping from verified bot configuration.
-- This migration does not create kick jobs.

begin;

create table if not exists public.canonical_group_map (
    group_code text not null,
    telegram_group_id text not null,
    group_name text not null,
    ordinal integer not null default 1,
    is_active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    primary key (group_code, telegram_group_id),
    constraint canonical_group_map_code_check
      check (group_code in ('COMBO_FULL', 'PRIME', 'BOY', 'REAL', 'ASIA', 'PINK_SPECIAL'))
);

insert into public.canonical_group_map (group_code, telegram_group_id, group_name, ordinal)
values
    ('COMBO_FULL', '-1003857691232', 'Prime', 1),
    ('COMBO_FULL', '-1003835994262', 'Boy', 2),
    ('COMBO_FULL', '-1003895162881', 'Real', 3),
    ('COMBO_FULL', '-1003865232620', 'Asia', 4),
    ('PRIME', '-1003857691232', 'Prime', 1),
    ('BOY', '-1003835994262', 'Boy', 1),
    ('REAL', '-1003895162881', 'Real', 1),
    ('ASIA', '-1003865232620', 'Asia', 1),
    ('PINK_SPECIAL', '-1004434723714', 'Pink Special', 1)
on conflict (group_code, telegram_group_id) do update
set group_name = excluded.group_name,
    ordinal = excluded.ordinal,
    is_active = true,
    updated_at = now();

-- Fill group_id only for single-group entitlements. Combo is deliberately
-- left null until it is expanded into one entitlement per target group.
update public.customer_entitlements_v2 e
   set group_id = m.telegram_group_id,
       updated_at = now()
  from canonical_group_map m
 where e.group_code = m.group_code
   and m.group_code <> 'COMBO_FULL'
   and m.is_active = true
   and e.group_id is null;

commit;

-- Verification queries:
-- select * from public.canonical_group_map order by group_code, ordinal;
-- select group_code, count(*) from public.customer_entitlements_v2
-- where source_quality = 'VERIFIED' group by group_code;
-- select count(*) from public.customer_entitlements_v2
-- where source_quality = 'VERIFIED' and group_id is null;
