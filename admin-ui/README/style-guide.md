# Prive Admin UI Style Guide

This app follows a single shared MUI-style visual system.

## Visual Direction

- Bright, clean, MUI-homepage-inspired UI
- Blue as the primary color
- Purple as the secondary accent
- White cards, subtle borders, soft shadows
- Rounded pills for tabs and chips
- Strong typography hierarchy with compact spacing

## Core Rules

- Prefer MUI components first: `Button`, `IconButton`, `TextField`, `Select`, `Tabs`, `Tab`, `Card`, `Chip`, `Dialog`, `Table`, `Stack`, `Box`
- Prefer theme overrides and `sx` for styling
- Use global CSS only for shell-level layout or truly cross-cutting resets
- Do not introduce new custom button/input CSS if a MUI component exists
- Keep primary actions contained, secondary actions outlined, destructive actions outlined with error color
- Keep dialog close buttons top-right, consistent size, and visually secondary
- Keep tables compact and readable with calm borders and controlled row spacing

## Shared Building Blocks

- `style-guide.ts` for tokens and rules
- `theme-registry.tsx` for global MUI theme overrides
- `dashboard-components.tsx` for reusable app wrappers:
  - `AppDialog`
  - `AppSection`
  - `AppToolbar`
  - `PanelHead`
  - `Metric`
  - `SimpleTable`
  - `Pagination`

## Spacing / Typography

- Headings should use bold weight and slightly negative letter spacing
- Dialog content should breathe with consistent vertical rhythm
- Use compact but not cramped spacing
- Prefer `body2` for descriptive helper text

## Color Usage

- `primary` for main navigation and primary actions
- `secondary` for supportive accent states
- `success`, `warning`, `error`, `muted` for statuses
- Avoid one-off hex colors unless they are added to the shared palette

## Date / Time

- Always format through shared helpers
- Never render raw ISO strings in tables or dialogs

## Recommended Pattern For New Screens

1. Build layout from `AppSection` and `AppToolbar`
2. Use `PanelHead` for section headers
3. Use `AppDialog` for modal work
4. Use shared status chips and shared table helpers
5. Keep page-level CSS minimal

## Anti-Patterns

- New custom button classes
- New ad-hoc input styling
- Raw `<button>` / `<input>` / `<select>` when MUI equivalents are available
- Mixing multiple color systems in the same view
- Raw date strings in UI
