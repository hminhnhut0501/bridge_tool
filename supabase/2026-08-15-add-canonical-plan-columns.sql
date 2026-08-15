-- Canonical plan metadata. Keep plan_name unchanged for rollback and audit.
alter table public.orders
  add column if not exists canonical_plan_family text,
  add column if not exists canonical_duration text,
  add column if not exists canonical_group_code text;

alter table public.renewal_kick_tasks_v2
  add column if not exists canonical_plan_family text,
  add column if not exists canonical_duration text,
  add column if not exists canonical_group_code text;

create index if not exists idx_orders_canonical_plan
  on public.orders (canonical_plan_family, canonical_duration, canonical_group_code);

create index if not exists idx_renewal_tasks_canonical_plan
  on public.renewal_kick_tasks_v2 (canonical_plan_family, canonical_duration, canonical_group_code);

-- Backfill only unambiguous names. Existing plan_name is never modified.
update public.orders
set
  canonical_plan_family = case
    when plan_name ilike '%pink%' or plan_name ilike '%hidden%' or plan_name ilike '%hg:%' then 'PINK'
    when plan_name ilike '%all access%' or plan_name ilike '%allaccess%' or plan_name ilike '%svip%' or plan_name ilike '%combo%' or plan_name ilike '%full 4%' then 'COMBO'
    when plan_name ilike '%prime%' then 'PRIME'
    when plan_name ilike '%boy%' then 'BOY'
    when plan_name ilike '%black%' or plan_name ilike '%real%' then 'REAL'
    when plan_name ilike '%asia%' then 'ASIA'
    else null
  end,
  canonical_duration = case
    when plan_name ilike '%trọn đời%' or plan_name ilike '%tron doi%' or plan_name ilike '%lifetime%' or plan_name ilike '%vĩnh viễn%' then 'LIFETIME'
    when regexp_match(lower(plan_name), '(\\d+)\\s*(ngày|ngay|day|days)') is not null then 'DAYS:' || (regexp_match(lower(plan_name), '(\\d+)\\s*(ngày|ngay|day|days)'))[1]
    when regexp_match(lower(plan_name), '(\\d+)\\s*(tháng|thang|month|months)') is not null then 'MONTHS:' || (regexp_match(lower(plan_name), '(\\d+)\\s*(tháng|thang|month|months)'))[1]
    when regexp_match(lower(plan_name), '(\\d+)\\s*(năm|nam|year|years)') is not null then 'YEARS:' || (regexp_match(lower(plan_name), '(\\d+)\\s*(năm|nam|year|years)'))[1]
    when plan_name ilike '%tùy chỉnh%' or plan_name ilike '%tuy chinh%' then 'CUSTOM'
    when plan_name ilike '%prime%' or plan_name ilike '%boy%' or plan_name ilike '%real%' or plan_name ilike '%black%' or plan_name ilike '%asia%' or plan_name ilike '%combo%' or plan_name ilike '%svip%' or plan_name ilike '%all access%' or plan_name ilike '%allaccess%' then 'CUSTOM'
    else 'REVIEW'
  end,
  canonical_group_code = case
    when plan_name ilike '%pink%' or plan_name ilike '%hidden%' or plan_name ilike '%hg:%' then 'PINK_SPECIAL'
    when plan_name ilike '%all access%' or plan_name ilike '%allaccess%' or plan_name ilike '%svip%' or plan_name ilike '%combo%' or plan_name ilike '%full 4%' then 'COMBO_FULL'
    when plan_name ilike '%prime%' then 'PRIME'
    when plan_name ilike '%boy%' then 'BOY'
    when plan_name ilike '%black%' or plan_name ilike '%real%' then 'REAL'
    when plan_name ilike '%asia%' then 'ASIA'
    else null
  end
where canonical_plan_family is null
   or canonical_duration is null
   or canonical_group_code is null;

update public.renewal_kick_tasks_v2
set
  canonical_plan_family = case
    when plan_name ilike '%pink%' or plan_name ilike '%hidden%' or plan_name ilike '%hg:%' then 'PINK'
    when plan_name ilike '%all access%' or plan_name ilike '%allaccess%' or plan_name ilike '%svip%' or plan_name ilike '%combo%' or plan_name ilike '%full 4%' then 'COMBO'
    when plan_name ilike '%prime%' then 'PRIME'
    when plan_name ilike '%boy%' then 'BOY'
    when plan_name ilike '%black%' or plan_name ilike '%real%' then 'REAL'
    when plan_name ilike '%asia%' then 'ASIA'
    else null
  end,
  canonical_duration = case
    when plan_name ilike '%trọn đời%' or plan_name ilike '%tron doi%' or plan_name ilike '%lifetime%' or plan_name ilike '%vĩnh viễn%' then 'LIFETIME'
    when regexp_match(lower(plan_name), '(\\d+)\\s*(ngày|ngay|day|days)') is not null then 'DAYS:' || (regexp_match(lower(plan_name), '(\\d+)\\s*(ngày|ngay|day|days)'))[1]
    when regexp_match(lower(plan_name), '(\\d+)\\s*(tháng|thang|month|months)') is not null then 'MONTHS:' || (regexp_match(lower(plan_name), '(\\d+)\\s*(tháng|thang|month|months)'))[1]
    when regexp_match(lower(plan_name), '(\\d+)\\s*(năm|nam|year|years)') is not null then 'YEARS:' || (regexp_match(lower(plan_name), '(\\d+)\\s*(năm|nam|year|years)'))[1]
    when plan_name ilike '%tùy chỉnh%' or plan_name ilike '%tuy chinh%' then 'CUSTOM'
    when plan_name ilike '%prime%' or plan_name ilike '%boy%' or plan_name ilike '%real%' or plan_name ilike '%black%' or plan_name ilike '%asia%' or plan_name ilike '%combo%' or plan_name ilike '%svip%' or plan_name ilike '%all access%' or plan_name ilike '%allaccess%' then 'CUSTOM'
    else 'REVIEW'
  end,
  canonical_group_code = case
    when plan_name ilike '%pink%' or plan_name ilike '%hidden%' or plan_name ilike '%hg:%' then 'PINK_SPECIAL'
    when plan_name ilike '%all access%' or plan_name ilike '%allaccess%' or plan_name ilike '%svip%' or plan_name ilike '%combo%' or plan_name ilike '%full 4%' then 'COMBO_FULL'
    when plan_name ilike '%prime%' then 'PRIME'
    when plan_name ilike '%boy%' then 'BOY'
    when plan_name ilike '%black%' or plan_name ilike '%real%' then 'REAL'
    when plan_name ilike '%asia%' then 'ASIA'
    else null
  end
where canonical_plan_family is null
   or canonical_duration is null
   or canonical_group_code is null;

comment on column public.orders.canonical_plan_family is 'COMBO, PRIME, BOY, REAL, ASIA, PINK';
comment on column public.orders.canonical_duration is '30D, LIFETIME, or REVIEW';
comment on column public.orders.canonical_group_code is 'Stable group routing code; plan_name remains display/history text.';
