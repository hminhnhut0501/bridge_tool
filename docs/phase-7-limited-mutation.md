# Phase 7: Limited Mutation

Phase 7 is the first phase that may call the new-core mutation workflow. It is
not enabled by default and requires all of these controls:

```env
RENEWAL_NEW_CORE_CANARY=ON
RENEWAL_NEW_CORE_DRY_RUN=OFF
RENEWAL_NEW_CORE_LIMITED_MUTATION=ON
RENEWAL_NEW_CORE_FULL_CUTOVER=OFF
RENEWAL_LIMITED_MUTATION_ACK=I_UNDERSTAND_LIMITED_MUTATION
RENEWAL_MUTATION_FREEZE=OFF
RENEWAL_NEW_CORE_COHORT_USER_IDS=...
```

The cohort must be explicit and small. Run the one-shot runner only after the
read-only canary has been reviewed:

```bash
python3.11 -m scripts.renewal_limited_mutation
```

Review the result before expanding the cohort. The global mutation freeze must
be turned OFF only for the explicitly approved one-shot window, then turned
back ON immediately afterward.
