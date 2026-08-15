# Phase 14: Legacy Sunset

Phase 14 adds a sunset gate over the remaining renewal legacy references. The
legacy boundary may remain during soak, but renewal task references, old kick
orchestration, and old renewal UI are blockers. Strict mode also blocks any
`support_events` reference.

```bash
python3.11 -m scripts.legacy_sunset_gate
python3.11 -m scripts.legacy_sunset_gate --strict
```

The gate is read-only. It does not delete files, alter data, or disable
unrelated support events. Cleanup proceeds only after each blocker has a
replacement in the new core.
