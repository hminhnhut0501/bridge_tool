# Phase 17: Limited Mutation

## Configuration

```text
RENEWAL_NEW_CORE_CANARY=ON
RENEWAL_NEW_CORE_DRY_RUN=OFF
RENEWAL_NEW_CORE_LIMITED_MUTATION=ON
RENEWAL_NEW_CORE_COHORT_USER_IDS=123,456
RENEWAL_NEW_CORE_COHORT_ORDER_IDS=
```

The cohort must contain at least one user ID or order ID. An empty cohort is a
hard error and cannot accidentally mean “all users”.

## Scope

Limited mutation processes only selected group tasks. It does not run the
global expiry reconcile, so unrelated expired orders cannot be mutated by this
phase.

All existing safety checks remain active:

- active-order retain;
- membership confirmation;
- retry/review transitions;
- state-machine validation.

Rollback is immediate by setting `RENEWAL_NEW_CORE_LIMITED_MUTATION=OFF` or
`RENEWAL_NEW_CORE_CANARY=OFF`.
