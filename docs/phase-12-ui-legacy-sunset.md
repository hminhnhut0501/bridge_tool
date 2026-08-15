# Phase 12: Renewal UI Legacy Sunset

The renewal tab now always renders `RenewalsSection` from the backend
`view_model`. Its actions call the v2 review/command endpoint; the UI does not
call Telegram or infer state from support events.

The old JSX remains only as source-level rollback material during the release
window. It is unreachable because `RENEWAL_UI_V2_ENABLED` is permanently true
in Phase 12 and should be physically removed after the release soak period.
