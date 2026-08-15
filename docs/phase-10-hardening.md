# Phase 10: Operational Hardening

Status: implemented on 2026-08-15

## Added controls

- `new_core/observability.py` converts cycle results into stable metrics.
- Structured cycle log includes correlation id, timestamp, success flag,
  metrics, and phase-specific errors.
- Stale-task detector flags processing/confirmation tasks with old, malformed,
  or missing transition timestamps.
- Feature-flag validator rejects ambiguous values instead of silently treating
  them as enabled.

## Operational minimum

The runtime should emit or persist these fields for every cycle:

- `correlation_id`
- `occurred_at`
- order/group scanned counts
- reconcile/task/kick counts
- blocked/review/retry/error counts
- expiry and kick error text

Alerts should be attached to stale tasks, review-required growth, repeated
confirmation unknowns, and cycles with zero activity beyond the expected
schedule window.

## Remaining deployment work

The utilities are tested but not yet connected to a metrics backend. Wiring
them into the production logger/monitor is deployment-specific and should be
done after the Phase 7 canary is enabled, so alert thresholds use real traffic
baseline rather than guessed values.
