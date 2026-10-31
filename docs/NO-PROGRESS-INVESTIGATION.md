# First-chunk FloodWait investigation — 2026-10-23

Observed job 1932: 122602795 bytes, zero bytes delivered, repeated GetFileRequest waits at offset zero. Four later jobs from the same source completed with one attempt. At 08:50 Telegram requested 6, 3 and 7 seconds, then the app imposed 3600 seconds. One lane and a 4-second shared media interval were already active. Disk had 3.7 GiB free. This points to first-chunk RPC throttling and an overly broad app cooldown, not verification or Drive throughput; it does not prove a file-specific Telegram restriction.

Telethon's installed implementation can raise FloodWaitError locally from its per-request-constructor deadline cache, as well as propagate a server RPC failure. Old diagnostics cannot distinguish those cases. New diagnostics include error class, traceback origin (cached branch vs RPC error path), request offset/limit, requested chunk offset, media DC, file size and lane. No file identifier/access hash/reference or request serialization is logged. Cached waits retain deadlines but do not count as new server incidents. Unknown versions safely report RPC error path, not a claim of observed network traffic.

Three consecutive waits before a lane's first chunk at offset zero yield the job for at least 30 minutes, with lower priority and no retry-budget consumption. Other jobs may run only after the existing account deadline expires. Once bytes have flowed, the existing in-stream continuation remains. A deferred job retains remote incomplete objects for normal cleanup/recovery; no completed backup is deleted.

Repeated media incidents use a 120-second minimum safety backoff rather than one hour; Telegram's requested time and all pre-existing longer account deadlines remain authoritative. Metadata repeated-FloodWait protection remains one hour. No API threshold or evasion is inferred. Account-wide media pacing and reduced lane count remain enabled.

Deployment moves the currently stuck zero-byte job 1932 to delayed retry only if it still matches that state, preserving the original account cooldown and user/source pauses. Production RPC behavior is not forcibly probed during the active cooldown. Next eligible jobs and newly attributed incidents will provide the remaining evidence.

Tests cover cached attribution/counting, first-chunk deferral/cleanup, priority and retry handling, exact in-stream resume, cancellation, shared deadline preservation and metadata cooldown compatibility.
