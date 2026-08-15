# Phase 14: Parent/Group Reconciliation

Status: dry-run implemented on 2026-08-15

## Checks

- expired orders without parent task;
- parent task without order;
- group task without parent;
- parent `total_groups` versus actual group task count;
- expected plan groups missing from group tasks;
- unexpected group tasks outside the current plan mapping.
- plan mapping unavailable for a task that already has group tasks.

## Safety

`parent_group_reconciliation.py` is read-only. It does not create missing
tasks, update counters, resolve states, or call Telegram. Any repair must be a
separate reviewed migration with a generated plan and rollback strategy.
