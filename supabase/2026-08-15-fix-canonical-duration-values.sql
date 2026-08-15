-- Recompute only canonical_duration after the duration parser was expanded.
-- plan_name remains unchanged.
update public.orders
set canonical_duration = case
  when plan_name ilike '%trọn đời%' or plan_name ilike '%tron doi%' or plan_name ilike '%lifetime%' or plan_name ilike '%vĩnh viễn%' then 'LIFETIME'
  when regexp_match(lower(plan_name), '(\\d+)\\s*(ngày|ngay|day|days)') is not null then 'DAYS:' || (regexp_match(lower(plan_name), '(\\d+)\\s*(ngày|ngay|day|days)'))[1]
  when regexp_match(lower(plan_name), '(\\d+)\\s*(tháng|thang|month|months)') is not null then 'MONTHS:' || (regexp_match(lower(plan_name), '(\\d+)\\s*(tháng|thang|month|months)'))[1]
  when regexp_match(lower(plan_name), '(\\d+)\\s*(năm|nam|year|years)') is not null then 'YEARS:' || (regexp_match(lower(plan_name), '(\\d+)\\s*(năm|nam|year|years)'))[1]
  when plan_name ilike '%tùy chỉnh%' or plan_name ilike '%tuy chinh%' then 'CUSTOM'
  when plan_name ilike '%prime%' or plan_name ilike '%boy%' or plan_name ilike '%real%' or plan_name ilike '%black%' or plan_name ilike '%asia%' or plan_name ilike '%combo%' or plan_name ilike '%svip%' or plan_name ilike '%all access%' or plan_name ilike '%allaccess%' then 'CUSTOM'
  else 'REVIEW'
end;

update public.renewal_kick_tasks_v2
set canonical_duration = case
  when plan_name ilike '%trọn đời%' or plan_name ilike '%tron doi%' or plan_name ilike '%lifetime%' or plan_name ilike '%vĩnh viễn%' then 'LIFETIME'
  when regexp_match(lower(plan_name), '(\\d+)\\s*(ngày|ngay|day|days)') is not null then 'DAYS:' || (regexp_match(lower(plan_name), '(\\d+)\\s*(ngày|ngay|day|days)'))[1]
  when regexp_match(lower(plan_name), '(\\d+)\\s*(tháng|thang|month|months)') is not null then 'MONTHS:' || (regexp_match(lower(plan_name), '(\\d+)\\s*(tháng|thang|month|months)'))[1]
  when regexp_match(lower(plan_name), '(\\d+)\\s*(năm|nam|year|years)') is not null then 'YEARS:' || (regexp_match(lower(plan_name), '(\\d+)\\s*(năm|nam|year|years)'))[1]
  when plan_name ilike '%tùy chỉnh%' or plan_name ilike '%tuy chinh%' then 'CUSTOM'
  when plan_name ilike '%prime%' or plan_name ilike '%boy%' or plan_name ilike '%real%' or plan_name ilike '%black%' or plan_name ilike '%asia%' or plan_name ilike '%combo%' or plan_name ilike '%svip%' or plan_name ilike '%all access%' or plan_name ilike '%allaccess%' then 'CUSTOM'
  else 'REVIEW'
end;
