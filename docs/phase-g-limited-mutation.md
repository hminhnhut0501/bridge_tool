# Phase G: Limited mutation

Mutation is protected by an explicit feature flag and a hard batch gate.

Initial production limits:

```text
enabled: false
max batch: 5
concurrency: 1
```

The gate refuses mutation when concurrency is greater than one or the batch
limit is greater than five. Enable only after the read-only canary has been
reviewed and keep a kill switch available.

This phase does not remove the legacy worker. It is a controlled experiment
with the new delayed-job table only.
