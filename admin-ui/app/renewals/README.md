# Renewal UI Contract

The renewal UI has two operator tabs:

- `expiring-soon`: expiry time and reminder delivery status;
- `expired`: membership, kick status, attempts, and last error.

Components must consume `RenewalViewModel` from `renewal-contract.ts`. They
must not infer state from `support_events`, raw `plan_name`, or legacy task
states. Until the new API is connected, `renewalFixture()` gives an explicit
API-contract warning instead of a misleading empty table.

Phase 2 components:

- `renewals-summary.tsx`
- `renewal-tabs.tsx`
- `renewal-filters.tsx`
- `renewal-state-panel.tsx`
- `renewal-tables.tsx`
- `renewal-detail-drawer-v2.tsx`
- `renewals-page-v2.tsx`
