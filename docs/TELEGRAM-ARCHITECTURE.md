# Telegram library decision

Choose Telethon 1.45.0 (pinned) for core + POC. It offers async 512 KiB
iter_download, persistent SQLite account sessions, explicit FloodWait, reconnect,
NewMessage/MessageEdited and raw MTProto forum functions. Python integrates
bounded async streaming with subprocess backpressure without a C++ toolchain.

TDLib is an actively developed official native library. Its download lifecycle
and disk/cache behavior would need an additional streaming-specific investigation.
Keep it as an alternative if real large-file acceptance reveals a Telethon issue.
Pyrogram upstream is archived and is not selected for new development.

Business logic depends on provider methods rather than raw Telethon objects.
Raw forum discovery uses the installed messages.GetForumTopicsRequest(peer=...),
paginates with date/message/topic offsets; General ID=1. Core stores numeric topic
IDs and derives message roots from forum reply headers. Normal groups use topic 0.
The older POC CLI intentionally lists at most 100 topics; Web core uses full
pagination. Every account operation shares persisted FloodWait and pacing, default
0.25 seconds; concurrency is one by default, capped at two. No bypass/rotation.

History bounded reverse iter_messages(min_id=checkpoint,max_id=target+1) pages
oldest-first; live never advances history checkpoint. Recent reconciliation
captures missed edits while incremental scanning captures all newer messages.
Credentials and session are private; service never requests interactive OTPs.

Primary references checked 2026-10-06:
- https://docs.telethon.dev/en/stable/modules/client.html
- https://docs.telethon.dev/en/stable/modules/events.html
- https://github.com/tdlib/td
- https://github.com/pyrogram/pyrogram
- https://rclone.org/commands/rclone_rcat/

Choice is supported by local mock+crypt tests, not a claim that real account/cloud
acceptance was performed without credentials.
