from __future__ import annotations

import argparse
import json

from scripts.legacy_sunset_scan import scan


DEFAULT_BLOCKING_PATTERNS = {"legacy_renewal_task", "old_scheduler_kick", "old_renewal_ui"}


def evaluate(report: dict, *, allow_legacy_boundary: bool = True) -> dict:
    blockers = []
    for path, findings in report.items():
        for pattern, count in findings.items():
            if pattern in DEFAULT_BLOCKING_PATTERNS and count:
                blockers.append({"file": path, "pattern": pattern, "count": count})
            if pattern == "support_events" and count and not allow_legacy_boundary:
                blockers.append({"file": path, "pattern": pattern, "count": count})
    return {
        "contract": "renewal_legacy_sunset_gate_v1",
        "ok": not blockers,
        "blockers": blockers,
        "legacy_boundary_allowed": allow_legacy_boundary,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate renewal legacy sunset readiness.")
    parser.add_argument("--strict", action="store_true", help="Treat support_events references as blockers too.")
    args = parser.parse_args()
    result = evaluate(scan(), allow_legacy_boundary=not args.strict)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
