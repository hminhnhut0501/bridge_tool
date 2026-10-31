# Broken pipe / Drive upload failure — 2026-10-07

VPS upload probe failed with Google 403 userRateLimitExceeded. Read-only remote stat succeeded; this does not establish the specific Google quota responsible. Python producer saw BrokenPipeError after rclone closed stdin, masking its stderr.

Fix: reap subprocess with a bounded wait, classify bounded stderr into safe storage categories, preserve generator/child cleanup and cancellation. Raw stderr is not persisted because it can expose remote paths or credentials. Classify rate limit, storage quota, authentication, permissions and network errors separately. Shared Drive rate-limit cooldown is 15/30/60 minutes, capped at one hour per failure; existing retry limit remains. Never shorten another job's longer shared cooldown.

Legacy recovery only selects FAILED/RETRY_WAIT jobs with exact BrokenPipeError and no pending user cancellation. Reset attempts and schedule after 15-minute cooldown. Preserve source/topic pause selection, cancelled/skipped jobs, completed backups and remote paths. Worker recovery handles interrupted active jobs; no file is marked completed without existing verification.

Tests: 69 backend tests PASS before final cooldown changes; 20 targeted storage/core tests PASS after final changes, including actual child stdin closure, sanitized error category, generator close, process reap, crypt roundtrip and shared cooldown protection. Deployment requires a graceful service restart and database backup. A Google-side limit may continue; recovery scheduling is not a claim that uploads have completed.
