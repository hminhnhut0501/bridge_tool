# Phase 17: Release report and push readiness

Build the final report after all checks:

```bash
python3.11 -m scripts.build_release_report \
  --backend-tests 1 \
  --frontend-typecheck 1 \
  --frontend-build 1 \
  --canary-cycles 3 \
  --output /tmp/renewal-release-report.json
```

Then run:

```bash
python3.11 -m scripts.final_product_gate \
  /tmp/renewal-release-report.json
git diff --check
```

Before commit, inspect `git status` and confirm no environment files, tokens,
service-role keys, production dumps, or temporary reports are staged.
