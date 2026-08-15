-- Phase 1: migration bundle verification.
-- Read-only checks; run after the entitlement migrations.

select to_regclass('public.customer_entitlements_v2') as entitlements_table;
select to_regclass('public.canonical_group_map') as group_map_table;
select to_regclass('public.entitlement_kick_jobs') as kick_jobs_table;

select
    count(*) as entitlement_rows,
    count(*) filter (where source_quality = 'VERIFIED') as verified_rows,
    count(*) filter (where state = 'REVIEW') as review_rows,
    count(*) filter (where not is_lifetime and expires_at is null) as invalid_timed_rows,
    count(*) filter (where group_id is null and source_quality = 'VERIFIED') as verified_missing_group
from public.customer_entitlements_v2;

select
    count(*) as job_rows,
    count(*) filter (where status = 'PENDING') as pending_jobs,
    count(*) filter (where status = 'RETRY') as retry_jobs,
    count(*) filter (where is_duplicate) as duplicate_job_keys
from (
    select
        j.id,
        j.status,
        count(*) over (partition by j.entitlement_id) > 1 as is_duplicate
    from public.entitlement_kick_jobs j
) jobs;

select source_order_id, group_code, count(*)
from public.customer_entitlements_v2
group by source_order_id, group_code
having count(*) > 1;
