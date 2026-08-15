# Phase 8: Limited Mutation Production

Phase 8 requires an explicit, reviewed cohort. The system must not infer a
production cohort from aggregate counts. Generate a preflight from the dry-run
report first:

```bash
python3.11 -m scripts.limited_mutation_preflight \
  /tmp/renewal-worker-dry-run.json \
  --max-cohort 5 \
  --output /tmp/limited-mutation-preflight.json
```

Only rows with `outcome=would_kick` are eligible. `unknown`, active-order,
mapping, invalid-identity, and review outcomes are excluded. The preflight is
read-only and requires human approval before setting the cohort environment.

After approval, run one-shot mutation with:

```env
RENEWAL_NEW_CORE_CANARY=ON
RENEWAL_NEW_CORE_DRY_RUN=OFF
RENEWAL_NEW_CORE_LIMITED_MUTATION=ON
RENEWAL_NEW_CORE_FULL_CUTOVER=OFF
RENEWAL_LIMITED_MUTATION_ACK=I_UNDERSTAND_LIMITED_MUTATION
RENEWAL_MUTATION_FREEZE=OFF
```

Immediately restore `RENEWAL_MUTATION_FREEZE=ON` after the one-shot run and
review attempts, task states, and Telegram results before expanding the cohort.
