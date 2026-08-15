from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FILES = [ROOT / "scheduler.py", ROOT / "scheduler_expiration_workflow.py", ROOT / "scheduler_kick_workflow.py", ROOT / "web_backend.py", ROOT / "admin-ui/app/page.tsx"]
PATTERNS = {
    "support_events": "support_events",
    "legacy_renewal_task": "renewal_kick_tasks",
    "old_scheduler_kick": "process_vip_kicks_for_expired_order",
    "old_renewal_ui": 'tab === "renewals" && !RENEWAL_UI_V2_ENABLED',
}


def scan():
    result = {}
    for path in FILES:
        text = path.read_text(encoding="utf-8")
        result[str(path.relative_to(ROOT))] = {name: text.count(pattern) for name, pattern in PATTERNS.items() if text.count(pattern)}
    return result


if __name__ == "__main__":
    print(json.dumps(scan(), ensure_ascii=False, indent=2, sort_keys=True))
