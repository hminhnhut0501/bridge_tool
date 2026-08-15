# Phase 5: Combo expansion

Every eligible Combo order must produce four target entitlements:

```text
PRIME
BOY
REAL
ASIA
```

The original `COMBO_FULL` row remains an audit parent and must not have a kick
job. Only child rows with a real `group_id` can produce delayed jobs.

The verification SQL must report:

```text
incomplete_combo_expansions = 0
combo_parent_jobs = 0
```
