# Phase 11: Limited mutation runner

This runner is the first component allowed to call the real worker with
mutation enabled. It remains disabled by default and requires both:

- a clean cutover decision;
- `MutationGate(enabled=True, max_batch=5, concurrency=1)`.

It executes exactly one batch and exits. Production must enable it only after
the Phase 10 preflight succeeds and a kill switch is available.
