# Phase 20: Legacy Sunset

## Guarded sunset

The renewal-specific legacy event writer is disabled only when explicitly
enabled:

```env
RENEWAL_LEGACY_SUNSET=ON
```

Support events unrelated to renewal/kick remain append-only and available for
the support log. This avoids disabling support audit globally.

## Scan

Run:

```bash
python3.11 -m scripts.legacy_sunset_scan
```

The scan reports remaining references to support events, legacy renewal task
names, old scheduler kick functions, and the old renewal UI fallback.

## Final deletion gate

Do not delete the old JSX or scheduler helpers until:

- full worker cutover is live and stable;
- legacy renewal event writes are zero;
- old task writes are zero;
- stale tasks are reconciled;
- UI v2 parity is accepted;
- rollback window has expired.
