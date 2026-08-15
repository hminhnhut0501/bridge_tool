# Phase 13: Full Worker Cutover

Phase 13 adds a preflight that combines static deployment flags with dynamic
health evidence. It does not enable full cutover or write production.

Required static configuration:

```text
RENEWAL_NEW_CORE_FULL_CUTOVER=ON
RENEWAL_NEW_CORE_DRY_RUN=OFF
RENEWAL_NEW_CORE_LIMITED_MUTATION=OFF
RENEWAL_NEW_CORE_CUTOVER_ACK=I_UNDERSTAND
```

Required dynamic evidence is evaluated by `dynamic_cutover_gate`. Any unknown
membership, duplicate claim, orphan task, attempt/finalizer error, or
out-of-cohort mutation blocks the preflight.
