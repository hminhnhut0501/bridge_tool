# Phase 15: Soak Validation

Before full worker cutover, collect at least four cycle reports and validate
them together:

```bash
python3.11 -m scripts.renewal_soak_report \
  /tmp/renewal-cycles.json \
  --minimum-cycles 4 \
  --output /tmp/renewal-soak-report.json
```

The soak fails on errors, unknown membership, duplicate claims, mutation
outside cohort, read-only writes, or an insufficient number of cycles.
