# Security

Single administrator: Argon2id password hash; opaque 256-bit random session token,
only SHA-256 token digest in SQLite; 12-hour expiry, HttpOnly, SameSite=Strict,
Secure in production. Mutation routes require session, matching CSRF token and
same-origin checks. Login allows five attempts per client per 15 minutes. Request
bodies are limited to 64 KiB even without Content-Length. Password hashing runs
off the event loop. API responses are no-store; CSP, frame denial and nosniff set.

Telegram authentication is available through authenticated, CSRF-protected Web UI or CLI. Pending challenges are scoped to the initiating web session and expire in 10 minutes; sends and verification attempts are rate limited. API credentials persist in a private 600 file; OTP/2FA are never persisted. API never returns Telegram API hash,
OTP/2FA, session bytes, OAuth tokens or crypt passwords. Config paths/secrets are
outside frontend settings. Provider errors become safe category names; rclone
stderr is bounded and never emitted. Logs contain event/job/source IDs only.

Paths are confined to configured root. Generated names normalize Unicode,
remove controls/bidi and filesystem separators, limit byte length and include
IDs. Original labels are React text nodes, not HTML. Subprocesses use argv arrays,
never a shell. Config must encrypt content, filenames and directory names.

CLI sets umask 077; keep data/session directories 700, DB/config/.env 600. SQLite
snapshots are security-sensitive, including auth hashes/sessions. rclone obscured
password values are not a substitute for filesystem protection. No RC server is
started. Production backend listens behind Nginx/Caddy HTTPS, not a development server.
Docker runs UID 10001 with no capabilities and private volumes.

Git/Docker/release packaging exclude secrets, sessions, caches and test data.
Do not expose the explicitly labeled mock test environment to production users.
No account/proxy rotation, rate-limit bypass or delete propagation is implemented.
