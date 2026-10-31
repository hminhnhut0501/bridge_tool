# In-stream FloodWait continuation

FloodPaused during download_chunk is handled inside the lane fetch, before yielding bytes. Retain the running job, upload subprocess, plaintext hash and progress counters. Wait for the shared persisted account deadline in cancellable sleeps of at most 30 seconds, rechecking deadline extensions. Recreate only the affected Telethon iterator at the exact undelivered offset; never assume a failed iterator preserved internal offset. Lane ordering and tail-size checks remain in force.

Emit transfer_chunk_waiting and transfer_chunk_resumed with internal job/source IDs and byte offset. An in-stream wait does not consume retry attempts or mark the job failed. Download preparation/metadata failures, genuine network errors, process death, restart and upload failures still use normal recovery, potentially from the beginning. This is not persistent byte-level resume across service restarts.

Upload rcat overrides network timeout to zero so an upstream Telegram pause does not trigger the old two-minute timeout. Pipe drain and final upload completion remain bounded to 180 seconds and classify stalls as upload_stalled; cancellation still reaps rclone and closes all lane iterators. Remote resumable-upload expiry or server-side errors can still force a normal retry.

Regression tests use a real local rclone crypt upload and a Telegram iterator that mutates its offset before throwing FloodWait. Assert ordered exact bytes, SHA-256, monotonically retained progress, retry offset and iterator cleanup. A separate test cancels while waiting on a 600-second FloodWait and verifies immediate cleanup.
