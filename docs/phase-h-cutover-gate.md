# Phase H: Cutover gate

The new worker cannot be enabled based on a single environment flag alone.
The cutover gate requires:

- no `REVIEW` or `UNKNOWN` canary decisions;
- no duplicate jobs;
- no missing group IDs among eligible jobs;
- mutation gate enabled with batch <= 5 and concurrency = 1.

If any condition fails, the gate returns explicit reasons and mutation must
remain disabled. This phase does not turn the flag on automatically.
