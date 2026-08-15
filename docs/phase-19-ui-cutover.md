# Phase 19: UI Cutover

## Feature flag

The new renewal section is selected with:

```env
NEXT_PUBLIC_RENEWAL_UI_V2=ON
```

When the flag is off, the existing renewal UI remains available as rollback.

## New section behavior

`renewals-section.tsx` renders:

- summary counters;
- task-first rows;
- normalized task state;
- `next_action` and blocker/error reason;
- kick and review mutations only when the view-model exposes them;
- no `support_events` state inference.

## Cutover safety

- The legacy UI is not deleted in this phase.
- UI rollback is `NEXT_PUBLIC_RENEWAL_UI_V2=OFF` followed by a frontend deploy.
- The flag must be tested against real `view_model` payloads before removal of
  the old JSX.

## Next sunset gate

Remove the old renewal block from `page.tsx` only after:

1. new UI row count matches backend view-model;
2. kick/review actions are verified in staging;
3. detail drawer and pagination parity are complete;
4. build and lint are clean;
5. rollback is no longer required.
