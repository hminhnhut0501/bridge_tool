# Phase 0: Renewal/Kick Baseline

Status: frozen on 2026-08-15

This document is the baseline for the renewal and kick rewrite. Phase 0 does
not change runtime behavior. Later phases must update this document when a
contract or migration gate is intentionally changed.

## Scope

The renewal lifecycle has four concerns:

1. Order expiry: `PAID` orders become `EXPIRED` when `expire_at` is reached.
2. Task planning: an expired order creates one v2 parent task and group tasks.
3. Telegram execution: a worker kicks, confirms, retries, or sends a task to review.
4. Administration: the API and renewal tab expose the task/read model.

`support_events` is a legacy append-only log. It is not a source of truth for
order state, kick state, retry decisions, or task finalization.

## Frozen state inventory

### Order state

The normalized core contract is:

| State | Meaning |
| --- | --- |
| `active` | A paid order currently grants access. |
| `expired` | The order is no longer valid. |
| `unknown` | The order cannot be safely classified. |

Storage values such as `PAID` and `EXPIRED` are adapter concerns and must be
normalized before reaching core logic.

### Normalized kick state

The admin/read-model contract is:

| State | Meaning |
| --- | --- |
| `none` | No actionable v2 kick state exists. |
| `processing` | Queued, executing, confirming, or retrying. |
| `done` | The group action is resolved, including retained access. |
| `blocked` | An active order prevents the kick. |
| `review_required` | Automatic processing cannot safely continue. |
| `failed_terminal` | Retry policy is exhausted or the failure is terminal. |

The raw task/group states remain storage detail. Phase 1 introduces the
explicit transition state machine in `new_core/state_machine.py`; the current
runtime writers are still compatibility callers until the later workflow
phases migrate them.

### Legacy aliases currently observed

These values are tracked for migration only and must not be expanded without a
contract change: `queued`, `running`, `pending`, `selected`, `waiting_confirm`,
`retry_pending`, `retry_scheduled`, `processing`, `kicked`, `retained`,
`blocked_active_order`, `unmapped`, `review`, `needs_review`, `need_review`,
`error`, and `failed`.

## Frozen event boundary

`support_events` may be used for:

- historical support-log display;
- append-only operational audit during migration;
- legacy migration diagnostics.

`support_events` must not be used for:

- deciding whether an order is expired;
- deciding whether a kick is due;
- retry/confirmation state;
- finalizing a v2 task;
- determining the admin renewal state.

## Time contract

- The canonical internal representation is timezone-aware UTC.
- The configured business timezone is used only at input/output boundaries.
- Naive datetimes and `replace(tzinfo=None)` are migration debt.
- `scheduler.now_local()`, `web_backend.now_local()`, and
  `web_backend.now_local_naive()` are temporary adapters, not core APIs.

The current configured production default is `Asia/Ho_Chi_Minh`.

## Current implementation baseline

Measured from the repository at freeze time:

| Area | Baseline |
| --- | --- |
| `scheduler.py` | 983 lines; still owns kick/membership orchestration. |
| `web_backend.py` | 4509 lines; routes, services, read models, and legacy boundary are mixed. |
| `admin-ui/app/page.tsx` | 13025 lines; renewal JSX is still embedded. |
| `admin-ui/app/renewals-section.tsx` | 160 lines; scaffold, not a complete replacement. |
| `admin_api_services.py` | 122 lines; currently imports builders from `web_backend.py`. |
| Core targeted tests | 43 tests passing at freeze. |
| Frontend build | Fails on `renewals-section.tsx` `any`/unused scaffold props. |
| Full test suite | Not green in the local environment; unrelated modules require missing `aiogram`/`requests`, and some legacy tests import removed scheduler helpers. |

Runtime database counts are intentionally not guessed from source code. Before
Phase 1 starts, collect them from the production read-only environment:

- orders by storage status and normalized state;
- `PAID` orders with `expire_at <= now`;
- v2 parent tasks by state;
- v2 group tasks by state;
- tasks with stale locks;
- tasks in `review_required` or terminal failure;
- members still present for resolved kick tasks;
- rows written to `support_events` by event type over the last 14 days.

## Phase 0 gates

Phase 0 is complete when:

1. This document is reviewed and treated as the baseline.
2. The contract freeze tests pass.
3. No new runtime state or event type is added without updating this document.
4. Production counts above are captured separately and attached to the release notes.
5. Phase 1 starts from this baseline and does not mix in UI or route extraction.
