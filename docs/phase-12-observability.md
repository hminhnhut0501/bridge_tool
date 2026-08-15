# Phase 12: Observability

The new worker must emit stable metrics:

```text
jobs_due
jobs_claimed
jobs_done
jobs_retained
jobs_review
jobs_retry
membership_unknown
telegram_rate_limit
duplicate_jobs
```

Logs must include `job_id`, `order_id`, `user_id`, `group_id`, decision,
reason, attempt, and duration. Secrets and raw Telegram exceptions must never
be logged.

Do not approve full cutover while duplicate jobs or Telegram rate limits are
non-zero in the observation window.
