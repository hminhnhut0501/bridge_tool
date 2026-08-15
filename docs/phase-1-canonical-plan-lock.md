# Phase 1: Canonical plan lock

## Contract

`plan_name` remains the original display and audit value. Kick logic must use
only the canonical columns.

Allowed plan families:

- `COMBO`
- `PRIME`
- `BOY`
- `REAL`
- `ASIA`
- `PINK`
- `UNSUPPORTED`

Allowed group codes:

- `COMBO_FULL`
- `PRIME`
- `BOY`
- `REAL`
- `ASIA`
- `PINK_SPECIAL`

Duration is represented as `LIFETIME`, `CUSTOM`, `REVIEW`, or a positive
quantity such as `DAYS:30`, `MONTHS:3`, or `YEARS:1`.

`UNSUPPORTED` and `REVIEW` rows are never eligible for automatic kick.

## Safety rule

This phase does not fill missing `expire_at`. A missing expiry is a lifecycle
data-quality issue and must be handled separately from plan mapping.
