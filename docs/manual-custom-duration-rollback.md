# Manual Custom Duration Rollback

The custom-duration manual order flow is guarded by `MANUAL_CUSTOM_DURATION_ENABLED`.

Normal state:

```text
MANUAL_CUSTOM_DURATION_ENABLED=ON
```

Rollback procedure:

1. Set `MANUAL_CUSTOM_DURATION_ENABLED` to `OFF` in the admin config.
2. Refresh Admin CP and mobile admin; the custom-duration option disappears.
3. Restart the bot process; custom-duration buttons disappear from the admin order wizard.
4. Confirm the backend returns HTTP 409 for any stale custom-duration request.
5. Continue monitoring existing custom orders. Their `plan_name`, `expire_at`, reminder, expired notice and kick processing are unchanged.

Recovery:

1. Set the config back to `ON`.
2. Refresh Admin CP/mobile and restart the bot process if needed.
3. Create one All Access custom order and one group custom order in a safe test account.
