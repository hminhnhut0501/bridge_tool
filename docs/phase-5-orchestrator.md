# Phase 5: Runtime Orchestrator

Status: implemented on 2026-08-15

## New boundary

`new_core/orchestrator.py` owns cycle ordering only:

1. run expiry reconciliation;
2. if expiry succeeds, run due kick groups;
3. preserve the successful phase result if the next phase fails;
4. return structured cycle results for logging/metrics.

It contains no database calls, Telegram calls, state literals beyond the
workflow boundary, or legacy-event behavior.

## Failure isolation

An expiry failure prevents kick execution for that cycle because kick tasks
may not have been reconciled. A kick failure does not erase a successful expiry
result; the next cycle can retry due tasks.

## Scheduler migration gate

The existing `scheduler.py` remains the compatibility runtime until production
implementations of `OrderRepository`, `KickTaskRepository`, and
`MembershipGateway` are wired and exercised in an integration environment.
The next migration step is to add those adapters and make the scheduler call
`run_renewal_cycle()` from one thin entry point, then delete the duplicated
legacy orchestration.
