# Phase 13: End-to-end gate

The final local gate covers the complete behavior:

1. expired entitlement is identified;
2. newer entitlement blocks an old order;
3. read-only canary reports `WOULD_KICK`;
4. worker checks membership;
5. worker kicks once and marks the job `DONE`.

The suite must also prove that the canary never calls the mutation adapter.
Only after this gate passes should production canary and limited mutation be
considered.
