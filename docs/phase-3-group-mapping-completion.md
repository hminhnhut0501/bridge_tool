# Phase 3: Group mapping completion

Before creating kick jobs, verify that every kickable entitlement has a
Telegram group ID. `COMBO_FULL` parent rows are excluded from this requirement
because they are audit parents; their child rows must have the four target
group IDs.

Required mappings:

```text
PRIME -> -1003857691232
BOY -> -1003835994262
REAL -> -1003895162881
ASIA -> -1003865232620
```

Pink remains `REVIEW` until its group ID and bot permissions are verified.

Current Pink mapping:

```text
PINK_SPECIAL -> -1004434723714
```

The mapping is known, but the bot's administrator permissions still need to be
verified before enabling Pink kick jobs.

The verification SQL is read-only and does not create jobs or call Telegram.
