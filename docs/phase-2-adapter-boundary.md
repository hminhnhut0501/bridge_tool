# Phase 2: Adapter Boundary

Status: implemented on 2026-08-15

## Objective

Keep the new core independent from Supabase, Telegram, Google Sheets, dotenv,
and the monolithic `scheduler`/`web_backend` modules.

## Ports

The contracts live in `new_core/ports.py`:

- `Clock`
- `OrderRepository`
- `KickTaskRepository`
- `MembershipGateway`
- `NotificationGateway`
- `LegacyEventSink`

Ports contain no database, framework, environment, or Telegram imports.

## Test adapters

`adapters/in_memory.py` provides deterministic fakes for unit tests. They are
not production replacements. They make it possible to test future expiry and
kick workflows without importing `scheduler.py` or requiring Supabase.

## Migration rule

New workflow code must receive ports as dependencies. It must not call:

- `import scheduler` for business behavior;
- `import web_backend` for read models or mutation behavior;
- `supabase_store` directly;
- `record_support_event` directly.

The current runtime modules remain compatibility callers until Phase 3 and
Phase 4 migrate their implementations to these ports.

## Gate

Phase 2 is complete when the port and fake-adapter tests pass. Production
Supabase/Telegram adapters are intentionally deferred to the workflow phases,
where their transaction and retry semantics can be tested against the locked
state machine.
