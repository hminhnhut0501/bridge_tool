# Phase D: Delayed kick worker

The worker processes only claimed jobs whose `run_at` is due. The batch is
bounded to a maximum of 50, with the default set to 10. Each job is resolved
against newer entitlements before membership is checked.

Outcomes:

- `DONE`: kicked successfully or already absent;
- `RETAINED`: a newer active entitlement exists;
- `RETRY`: Telegram or adapter failure;
- `REVIEW`: incomplete entitlement or unknown membership.

The caller schedules this worker periodically. The worker itself never loops
forever and never scans the whole orders table.
