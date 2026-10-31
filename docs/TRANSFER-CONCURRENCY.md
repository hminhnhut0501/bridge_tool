# Configurable transfer concurrency

Settings → Nhịp tải contains File tải/upload song song, integer range 1–4. Recommended range 1–2 for this account/VPS; start at one when FloodWait is frequent. Three or four increase concurrent buffering/upload pressure and do not guarantee higher aggregate speed because Telegram media pacing and account cooldown remain shared.

PATCH /api/settings accepts optional concurrency, validates 1–4, persists it in runtime_settings, resizes live transfer capacity, and recalculates per-new-upload bandwidth allocation. Existing uploads retain the bandwidth flags they started with. New workers are supervised and spawned only when needed; lowering capacity does not cancel running jobs. Existing transfer holders finish/handoff before new claims are allowed. The one verification slot is independent, so total active jobs can exceed configured transfer concurrency by one.

Startup applies persisted concurrency before initializing the limiter and workers. No service restart is required for subsequent UI changes. Scheduler/source pauses, random rests and FloodWait deadlines are not cleared. Environment DOWNLOAD_CONCURRENCY supports 1–4 as well.

Regression tests cover grow/shrink with active holders, integer bounds, settings persistence, live worker growth, health readiness after reducing concurrency, and existing pipeline/cancellation behavior.
