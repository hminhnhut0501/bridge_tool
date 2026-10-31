# Compact overview — 2026-10-07

Overview now has a single lifecycle status with a live mm:ss countdown; three clickable metrics; compact file rows distinguishing transfer percentage and indeterminate verification; five recent meaningful events with repeated scans grouped; and a compact Telegram/remote/concurrency footer. Removed storage sidebar, RAM/uptime block, duplicated speed/byte totals, misleading backup-percentage storage gauge and raw Job/Source identifiers. Storage and system details remain on their dedicated pages. Existing queue controls and transfer-page cards unchanged.

Validation: TypeScript/Vite build PASS; 3 isolated Playwright E2E PASS, including mixed transfer/verification and rest countdown, no false verification percentage, three metrics, removed old panels, mobile overflow, existing crypt pipeline/queue/auth flows. Desktop/mobile screenshots reviewed. Frontend-only deployment requires no worker restart.
