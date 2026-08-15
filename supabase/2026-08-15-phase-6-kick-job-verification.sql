-- Phase 6: kick job verification. Read-only.

select
    j.status,
    count(*) as job_count
from public.entitlement_kick_jobs j
group by j.status
order by j.status;

select count(*) as duplicate_job_entitlements
from (
    select entitlement_id
    from public.entitlement_kick_jobs
    group by entitlement_id
    having count(*) > 1
) duplicates;

select count(*) as invalid_jobs
from public.entitlement_kick_jobs j
join public.customer_entitlements_v2 e on e.id = j.entitlement_id
where e.is_lifetime
   or e.expires_at is null
   or e.group_id is null
   or e.source_quality <> 'VERIFIED'
   or e.state not in ('ACTIVE', 'EXPIRED');

select count(*) as parent_combo_jobs
from public.entitlement_kick_jobs j
where j.group_code = 'COMBO_FULL';

select
    j.group_code,
    j.group_id,
    j.status,
    count(*) as job_count
from public.entitlement_kick_jobs j
group by j.group_code, j.group_id, j.status
order by j.group_code, j.group_id, j.status;
