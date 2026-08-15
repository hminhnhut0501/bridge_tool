# Phase 2: Renewal State Ledger

Phase 2 introduces a read-only ledger contract over orders, renewal parent
tasks, group tasks, and attempts. It deliberately does not read
`support_events` and does not write any table or Telegram state.

Run it with:

```bash
python3.11 -m scripts.renewal_state_ledger > /tmp/renewal-state-ledger.json
```

The report exposes normalized states, missing parents/orders, duplicate keys,
stale locks, and attempt states. It is the sole input for later repair-plan
generation; no repair should be inferred from aggregate counts alone.
