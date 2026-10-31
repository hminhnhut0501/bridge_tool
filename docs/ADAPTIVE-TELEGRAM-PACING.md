# Adaptive Telegram pacing and diagnostics

Media iterator advances share an account-wide start gate, separate from metadata serialization. Initially start at most one advance per 250ms across all jobs. This is not a fixed bytes/sec cap or exact RPC count: Telethon iterators can buffer data or issue multiple requests internally. Concurrent calls may overlap after starting; existing bounded lanes and streaming buffers still apply.

On a distinct FloodWait, double the media interval (cap 4 seconds), reduce media lanes, persist the last incident and retain the longest shared Telegram deadline. Keep the repeated-incident safety cooldown. After ten quiet minutes and a successful media call, reduce the interval by 10%, never below 250ms; further increases in speed require another ten quiet minutes. No automatic lane increase is performed. Pause/stop states and FloodWait deadlines remain respected.

A structured telegram_flood_diagnostic warning records the actual exception request class when available, labelled operation, stage, internal job/source IDs, Telegram wait, app cooldown, recent wrapper call count, media wrapper call count, interval and lanes. Wrapper counts are not claimed to be wire-level RPC counts. No request serialization, media location, filename, phone, caption, session or credential is logged. Concurrent duplicates still share a single incident record.

The latest diagnostic is persisted and accessible to an authenticated admin at GET /api/telegram/rate-status. History includes a concise method/stage and wait summary. Unknown request classes remain null instead of guessing. Existing old history cannot be retroactively attributed to a method.

Regression tests cover account-wide chunk spacing across jobs, actual request-class diagnostics, persisted slowdown, gradual quiet-period recovery, concurrent burst deduplication, deadline preservation, ordered output and cancellation cleanup.
