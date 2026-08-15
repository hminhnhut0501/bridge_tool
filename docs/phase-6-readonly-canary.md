# Phase 6: Read-only Canary

The canary runner executes exactly one new-core read-only cycle. It refuses to
run unless canary and dry-run are enabled and limited/full mutation are off.
It also fails unless the result is `read_only` with zero Supabase writes and
zero Telegram mutations.

```bash
export RENEWAL_NEW_CORE_CANARY=ON
export RENEWAL_NEW_CORE_DRY_RUN=ON
export RENEWAL_NEW_CORE_LIMITED_MUTATION=OFF
export RENEWAL_NEW_CORE_FULL_CUTOVER=OFF
export RENEWAL_MUTATION_FREEZE=ON

python3.11 -m scripts.renewal_readonly_canary \
  > /tmp/renewal-readonly-canary.json
```
