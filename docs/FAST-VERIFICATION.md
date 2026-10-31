# Fast verification

Fresh uploads use rclone crypt's encrypted-content checksum verification, followed by logical size and stable remote object ID checks after promotion. Plaintext SHA-256 is still computed from the upload stream. On Drive, a successful checksum receipt plus unchanged object ID and size eliminates full remote rereads.

The receipt is ephemeral, bound to the unique temporary filename and the crypt backend's checksum-success log. Only supported digest formats from crypt/crypt.go are accepted; generic transfer success and size logs are not proof. Upload failure invalidates the receipt. rclone is invoked with checksum checking explicitly enabled.

If no receipt exists, verify the temporary file's plaintext SHA-256 before promotion. After promotion, a stable ID permits reusing that verification; missing or changed IDs require checking final content. Recovery also checks actual remote contents. Existing final conflicts remain protected. Backends without stable IDs may still require two reads.

Encrypted MD5 is a transport checksum, not a plaintext SHA-256 readback. This path trusts rclone's crypt implementation and Drive object identity. The implementation was verified against rclone v1.75.1 backend/crypt/crypt.go (put and PutStream). Unsupported log formats safely fall back to reading contents.

Reference: https://github.com/rclone/rclone/blob/v1.75.1/backend/crypt/crypt.go

Regression coverage includes zero readback for checksum-verified stable IDs, missing receipts, changed identity and corruption, receipt source/name binding, and recovery of corrupted temporary files.
