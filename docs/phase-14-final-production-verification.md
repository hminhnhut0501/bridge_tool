# Phase 14: Full production verification

Build a JSON release report containing migration, canary, metrics, backend,
and frontend results, then run:

```bash
python3.11 -m scripts.final_product_gate /tmp/renewal-release-report.json
```

The gate requires:

- at least three canary cycles;
- zero duplicate jobs;
- zero invalid timed entitlements;
- zero unsupported kickable entitlements;
- zero incorrect kicks;
- zero legacy mutations;
- zero data-loss events;
- backend tests pass;
- frontend typecheck passes;
- frontend build passes.

This gate never enables mutation or deploys automatically.
