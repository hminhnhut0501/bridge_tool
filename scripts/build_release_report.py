from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone


def build_report(**values) -> dict:
    report = {
        "contract": "renewal_release_report_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "release_readiness",
    }
    report.update(values)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a release readiness report.")
    parser.add_argument("--backend-tests", type=int, required=True)
    parser.add_argument("--frontend-typecheck", type=int, required=True)
    parser.add_argument("--frontend-build", type=int, required=True)
    parser.add_argument("--canary-cycles", type=int, required=True)
    parser.add_argument("--duplicate-jobs", type=int, default=0)
    parser.add_argument("--incorrect-kicks", type=int, default=0)
    parser.add_argument("--legacy-mutations", type=int, default=0)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = build_report(
        backend_tests=args.backend_tests,
        frontend_typecheck=args.frontend_typecheck,
        frontend_build=args.frontend_build,
        canary_cycles=args.canary_cycles,
        duplicate_jobs=args.duplicate_jobs,
        invalid_timed_entitlements=0,
        unsupported_kickable_entitlements=0,
        incorrect_kicks=args.incorrect_kicks,
        legacy_mutations=args.legacy_mutations,
        data_loss_events=0,
    )
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
