# rclone storage

Use a named crypt remote, e.g. `crypt:`. Config must be readable by the service
user and have no group/other permission bits. This implementation reads normal
rclone INI config; password-encrypted rclone config files are not supported.
Do not place config in an image, public directory or Git repository.

```ini
[crypt]
type = crypt
remote = gdrive:TelegramVault
filename_encryption = standard
directory_name_encryption = true
password = <rclone-obscured-value>
password2 = <rclone-obscured-value>
```

Create the config with `rclone config`, not by copying placeholder passwords.
The application refuses a plain Drive remote or filename/directory encryption
disabled. Default logical root TelegramVault_TEST confines local/development
writes. Configure a separate root and DB for production before adding sources.

Streaming uses `rcat --size <known-plaintext-bytes> --buffer-size 1M
--drive-chunk-size 8M --transfers 1 --retries 1`. Known size avoids unknown-size
spooling behavior. Application upload caps use a literal B suffix (rclone's
bare numeric bandwidth values mean KiB/s). Remote error details stay private;
only classified errors such as google_rate_limit are recorded.

`lsjson --stat` through crypt reports logical plaintext size. `cat` through crypt
provides plaintext to a bounded SHA-256 reader, never a full local file.
`moveto --immutable` promotes verified temporary objects. Existing final objects
need the known digest and size; conflicts fail rather than overwrite.

Official references:
- https://rclone.org/commands/rclone_rcat/
- https://rclone.org/commands/rclone_lsjson/
- https://rclone.org/crypt/
- https://rclone.org/docs/#bwlimit-bandwidth-spec

The current implementation does not expose rclone RC. OAuth refresh updates the
config, so production config must be mounted **read-write** to the service user
if the Drive remote needs token refresh. The container still restricts access to
that private directory. Local crypt-only config needs no token refresh.
