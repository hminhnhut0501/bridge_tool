-- Phase 2: move canonical DB keys from ALL_ACCESS_* to COMBO_* and remove the legacy rows.
-- Run this after code paths have switched to the Combo names or when config_aliases already maps them.

begin;

insert into public.bot_config (key, value, updated_at)
select 'PLAN_COMBO_30D', value, coalesce(updated_at, now())
from public.bot_config
where key = 'PLAN_ALL_ACCESS_30D'
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'PLAN_COMBO_LIFE', value, coalesce(updated_at, now())
from public.bot_config
where key = 'PLAN_ALL_ACCESS_LIFE'
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'PLAN_COMBO_30D_ALIASES', value, coalesce(updated_at, now())
from public.bot_config
where key = 'PLAN_ALL_ACCESS_30D_ALIASES'
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'PLAN_COMBO_LIFE_ALIASES', value, coalesce(updated_at, now())
from public.bot_config
where key = 'PLAN_ALL_ACCESS_LIFE_ALIASES'
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'PRICE_COMBO_30D', value, coalesce(updated_at, now())
from public.bot_config
where key = 'PRICE_ALL_ACCESS_30D'
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'PRICE_COMBO_LIFE', value, coalesce(updated_at, now())
from public.bot_config
where key = 'PRICE_ALL_ACCESS_LIFE'
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'PRICE_COMBO_30D_USD', value, coalesce(updated_at, now())
from public.bot_config
where key = 'PRICE_ALL_ACCESS_30D_USD'
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'PRICE_COMBO_LIFE_USD', value, coalesce(updated_at, now())
from public.bot_config
where key = 'PRICE_ALL_ACCESS_LIFE_USD'
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'BTN_BUY_COMBO_30D', value, coalesce(updated_at, now())
from public.bot_config
where key = 'BTN_BUY_ALL_ACCESS_30D'
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'BTN_BUY_COMBO_LIFE', value, coalesce(updated_at, now())
from public.bot_config
where key = 'BTN_BUY_ALL_ACCESS_LIFE'
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'BTN_VIEW_COMBO_PAGE', value, coalesce(updated_at, now())
from public.bot_config
where key = 'BTN_VIEW_ALL_ACCESS_PAGE'
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'TXT_COMBO_DESCRIPTION', value, coalesce(updated_at, now())
from public.bot_config
where key = 'TXT_ALL_ACCESS_DESCRIPTION'
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

insert into public.bot_config (key, value, updated_at)
select 'IMG_COMBO_PAGE', value, coalesce(updated_at, now())
from public.bot_config
where key = 'IMG_ALL_ACCESS_PAGE'
on conflict (key) do update
set value = excluded.value,
    updated_at = now();

delete from public.bot_config
where key in (
  'PLAN_ALL_ACCESS_30D',
  'PLAN_ALL_ACCESS_LIFE',
  'PLAN_ALL_ACCESS_30D_ALIASES',
  'PLAN_ALL_ACCESS_LIFE_ALIASES',
  'PRICE_ALL_ACCESS_30D',
  'PRICE_ALL_ACCESS_LIFE',
  'PRICE_ALL_ACCESS_30D_USD',
  'PRICE_ALL_ACCESS_LIFE_USD',
  'BTN_BUY_ALL_ACCESS_30D',
  'BTN_BUY_ALL_ACCESS_LIFE',
  'BTN_VIEW_ALL_ACCESS_PAGE',
  'TXT_ALL_ACCESS_DESCRIPTION',
  'IMG_ALL_ACCESS_PAGE'
);

commit;
