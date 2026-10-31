# Compact transfer list — 2026-10-07

Replaced two presentation cards with one aligned list. Desktop rows stay under 130px, icons are 32px, names ellipsize with full tooltip, progress is 4px with subdued glow. Removed per-file encryption label and nested progress background. Status, speed, total bytes and menu occupy a stable right column. Verification remains indeterminate, with no transfer speed or duplicate status text. Active tab now says “Đang xử lý” to include verification. Mobile keeps progress and data below the name; action target remains 44px. Existing cancellation modal and focus handling preserved.

TypeScript/Vite build and 3 isolated Playwright E2E PASS. Added geometry assertions for stacked rows, row height and right-aligned menu; retained mobile overflow, verification, queue and cancellation checks. Desktop/mobile screenshots reviewed. Frontend-only deployment, no worker restart.
