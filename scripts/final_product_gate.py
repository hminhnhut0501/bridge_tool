from __future__ import annotations

import argparse
import json


def evaluate(report: dict) -> tuple[bool, list[str]]:
    reasons = []
    required_zero = (
        "duplicate_jobs",
        "invalid_timed_entitlements",
        "unsupported_kickable_entitlements",
        "incorrect_kicks",
        "legacy_mutations",
        "data_loss_events",
    )
    for key in required_zero:
        if int(report.get(key, 0)) != 0:
            reasons.append(f"{key} != 0")
    if int(report.get("canary_cycles", 0)) < 3:
        reasons.append("canary_cycles < 3")
    if int(report.get("frontend_typecheck", 0)) != 1:
        reasons.append("frontend_typecheck not passed")
    if int(report.get("frontend_build", 0)) != 1:
        reasons.append("frontend_build not passed")
    if int(report.get("backend_tests", 0)) != 1:
        reasons.append("backend_tests not passed")
    return not reasons, reasons


def main() -> int:
    parser = argparse.ArgumentParser(description="Final product release gate; read-only.")
    parser.add_argument("report")
    args = parser.parse_args()
    with open(args.report, encoding="utf-8") as handle:
        report = json.load(handle)
    allowed, reasons = evaluate(report)
    print(json.dumps({"allowed": allowed, "reasons": reasons, "mode": "verification_only"}, ensure_ascii=False, indent=2))
    return 0 if allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())
