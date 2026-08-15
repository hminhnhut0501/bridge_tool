# Phase K: Legacy sunset gate

Legacy may be deleted or permanently disabled only after the new worker has
completed at least three observation cycles and all safety counters are zero.

Required zero counters:

- incorrect kicks;
- unresolved reviews;
- legacy mutations;
- data-loss events.

If any counter is non-zero, legacy remains read-only and available for audit or
rollback.
