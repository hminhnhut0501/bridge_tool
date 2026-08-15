# Phase 10: Metrics and Dynamic Health Gate

Phase 10 adds operational metrics and a dynamic full-cutover gate. Static
feature flags alone are insufficient. Full worker cutover must be blocked when
there are duplicate claims, orphan tasks, attempt/finalizer failures, unknown
membership, or mutation outside the approved cohort.

Required evidence fields:

```text
baseline_available
duplicate_claims
orphan_tasks
attempt_write_failures
finalizer_failures
unknown_membership
mutation_outside_cohort
```
