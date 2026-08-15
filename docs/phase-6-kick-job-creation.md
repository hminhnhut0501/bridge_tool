# Phase 6: Kick job creation

Kick jobs are created only from complete child entitlements:

- `source_quality = VERIFIED`;
- state is `ACTIVE` or `EXPIRED`;
- timed plan with `expires_at`;
- non-null `group_id`;
- not the `COMBO_FULL` audit parent.

Required verification results:

```text
duplicate_job_entitlements = 0
invalid_jobs = 0
parent_combo_jobs = 0
```

This phase schedules work only. It does not call Telegram and does not claim
or execute jobs.
