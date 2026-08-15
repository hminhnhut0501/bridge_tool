# Phase C: Delayed kick jobs

`entitlement_kick_jobs` is the only schedule consumed by the rebuilt worker.
One entitlement produces at most one job.

Jobs are created only when the entitlement is verified, timed, and has a
canonical `group_id`. Lifetime, `REVIEW`, `UNSUPPORTED`, missing-expiry, and
missing-group rows produce no job.

This phase schedules work at `expires_at`; it does not execute Telegram
mutations. The worker and rate limiter are separate phases.
