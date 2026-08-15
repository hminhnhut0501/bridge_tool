# Phase 6: Production Adapters

Status: implemented on 2026-08-15

## Adapters

- `adapters/supabase_renewal.py` maps the existing Supabase store API to the
  Phase 2 order/task repository ports.
- `adapters/telegram_membership.py` maps Telegram member lookup and ban/unban
  to `MembershipGateway`.

The adapters are the only new-core layer that knows the existing infrastructure
method names.

## Conservative Telegram behavior

- known absent member -> `False`;
- known present member -> `True`;
- temporary/unknown Telegram error -> `None`;
- unknown presence is handled by the workflow as `review_required`;
- kick errors return a failed `KickResult` for retry handling.

## Migration status

The adapters are implemented and tested with fakes. They are not yet wired as
the default production scheduler dependencies because the existing scheduler
still owns active-order membership policy, support grace, and legacy logging.
That wiring belongs to the scheduler cutover gate after the compatibility
behavior is covered by integration tests.
