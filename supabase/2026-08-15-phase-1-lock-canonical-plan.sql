-- Phase 1: lock the canonical plan contract.
-- plan_name remains untouched. This migration only updates canonical columns.
-- Run in Supabase SQL Editor after reviewing the preview queries below.

begin;

-- Signature has no approved group routing yet. Keep it out of kick decisions.
update public.orders
   set canonical_plan_family = 'UNSUPPORTED',
       canonical_group_code = null,
       canonical_duration = case
           when plan_name ilike '%trọn đời%'
             or plan_name ilike '%tron doi%'
             or plan_name ilike '%lifetime%'
             or plan_name ilike '%vĩnh viễn%'
           then 'LIFETIME'
           else 'REVIEW'
       end
 where order_id::text in ('1778511331', '1778502232')
   and status = 'CANCELLED';

-- The same protection applies to any future Signature row.
update public.orders
   set canonical_plan_family = 'UNSUPPORTED',
       canonical_group_code = null,
       canonical_duration = case
           when plan_name ilike '%trọn đời%'
             or plan_name ilike '%tron doi%'
             or plan_name ilike '%lifetime%'
             or plan_name ilike '%vĩnh viễn%'
           then 'LIFETIME'
           else 'REVIEW'
       end
 where (plan_name ilike '%signature%' or plan_name ilike '%privé signature%')
   and (canonical_plan_family is null or canonical_plan_family = 'UNSUPPORTED');

-- Reject values outside the canonical vocabulary while retaining NULL for
-- legacy rows that still require review.
alter table public.orders
  drop constraint if exists orders_canonical_plan_family_check;
alter table public.orders
  add constraint orders_canonical_plan_family_check
  check (canonical_plan_family is null or canonical_plan_family in
    ('COMBO', 'PRIME', 'BOY', 'REAL', 'ASIA', 'PINK', 'UNSUPPORTED'));

alter table public.orders
  drop constraint if exists orders_canonical_duration_check;
alter table public.orders
  add constraint orders_canonical_duration_check
  check (canonical_duration is null
    or canonical_duration in ('LIFETIME', 'CUSTOM', 'REVIEW')
    or canonical_duration ~ '^(DAYS|MONTHS|YEARS):[1-9][0-9]*$');

alter table public.orders
  drop constraint if exists orders_canonical_group_code_check;
alter table public.orders
  add constraint orders_canonical_group_code_check
  check (canonical_group_code is null or canonical_group_code in
    ('COMBO_FULL', 'PRIME', 'BOY', 'REAL', 'ASIA', 'PINK_SPECIAL'));

commit;
