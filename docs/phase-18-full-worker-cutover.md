# Phase 18: Full Worker Cutover

## Cutover contract

The scheduler can use the new-core worker as the only renewal worker only when
all explicit gates pass:

```env
RENEWAL_NEW_CORE_FULL_CUTOVER=ON
RENEWAL_NEW_CORE_DRY_RUN=OFF
RENEWAL_NEW_CORE_LIMITED_MUTATION=OFF
RENEWAL_NEW_CORE_CUTOVER_ACK=I_UNDERSTAND
```

If the full flag is set but any gate fails, the scheduler stops the renewal
cycle and logs a blocking error. It does not silently fall back to the old
worker, because mixed workers could process the same task concurrently.

## Pre-production conditions

Before enabling:

- stale task audit completed;
- plan mapping unavailable is zero;
- expired orders missing tasks have a reviewed repair plan;
- parent/group parity is clean;
- read-only canary has completed a full expiry window;
- limited mutation has no unsafe mismatch;
- rollback window and operator are assigned.

Rollback is an explicit config change back to `RENEWAL_NEW_CORE_FULL_CUTOVER=OFF`
followed by process restart. Do not run old and new mutation workers together.
