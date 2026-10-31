# Encryption and integrity

Encryption is implemented exclusively by rclone crypt. Logical paths remain in
private SQLite and authenticated UI; underlying storage sees ciphertext names
and ciphertext content. File sizes and modification time are not hidden by crypt.
Never treat the encrypted Google object hash as a plaintext hash.

SHA-256 is accumulated from incoming plaintext chunks. Completion requires exact
input length, rclone success, crypt logical size and verification policy. Default
full mode hashes decrypted temporary object, promotes, then hashes final object.
Size-only mode reduces verification traffic, but has weaker content assurance.
Recovering an existing final/incomplete object always requires a persisted SHA-256
match. Missing hash is not inferred from size alone.

If interruption happens before digest persistence, retry uses a new incomplete
UUID. Orphan incomplete objects are not completed and not blindly deleted.
Restore keys separately and retain both crypt passwords/salt; loss of keys makes
stored ciphertext irrecoverable. Telegram sessions are never uploaded by default.
