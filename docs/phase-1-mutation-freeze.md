# Phase 1: Renewal Mutation Freeze

The new-core runtime now has a fail-closed emergency stop controlled by
`RENEWAL_MUTATION_FREEZE`.

For the freeze window, set:

```env
RENEWAL_MUTATION_FREEZE=ON
RENEWAL_NEW_CORE_CANARY=OFF
RENEWAL_NEW_CORE_LIMITED_MUTATION=OFF
RENEWAL_NEW_CORE_FULL_CUTOVER=OFF
```

When enabled, both the full new-core cycle and limited mutation cycle raise
before constructing repositories or calling Telegram. Read-only audit scripts
remain available.
