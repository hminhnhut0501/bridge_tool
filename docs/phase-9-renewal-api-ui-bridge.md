# Phase 9: Renewal API/UI Bridge

Status: bridge implemented on 2026-08-15

## Completed

- `/admin-api/renewal-kick-v2` now returns `view_model` alongside the legacy
  `view` response.
- The new payload is produced by `new_core.renewal_view_model` and has
  `schema_version: 1`.
- `renewals-section.tsx` no longer contains explicit `any` types.
- Admin UI production build passes.

## Intentionally not completed in this bridge

The old renewal JSX is still present in `page.tsx`, and
`renewals-section.tsx` is not yet the full table/action replacement. This is
intentional: removing the old block before the new component renders every
row action would be a functional regression.

## Cutover gate

The remaining UI work must:

1. render the complete table from `view_model.rows`;
2. map `next_action` to allowed mutations;
3. move detail/timeline rendering into the new section;
4. compare old/new row counts and action availability;
5. remove the renewal JSX and unused renewal state from `page.tsx`.
