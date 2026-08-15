# Phase 4: Parent/Group Reconciliation

Phase 4 validates the relationship between renewal orders, parent renewal
tasks, and group tasks without performing writes or Telegram mutations.

It reports orphan groups, parents without groups, user mismatches, duplicate
`task_id + group_id` keys, and a row-level parent summary. The report is a
precondition for any future repair operation.

Run:

```bash
python3.11 -m scripts.parent_group_reconciliation \
  --output /tmp/parent-group-reconciliation.json
```
