from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone


def build_soak_report(cycles: list[dict], *, minimum_cycles: int = 4) -> dict:
    errors = []
    if len(cycles) < minimum_cycles:
        errors.append(f"at least {minimum_cycles} cycles are required")
    for index, cycle in enumerate(cycles, start=1):
        if cycle.get("errors"):
            errors.append(f"cycle {index} has errors")
        if cycle.get("unknown_membership", 0):
            errors.append(f"cycle {index} has unknown membership")
        if cycle.get("duplicate_claims", 0):
            errors.append(f"cycle {index} has duplicate claims")
        if cycle.get("mutation_outside_cohort", 0):
            errors.append(f"cycle {index} mutated outside cohort")
        if cycle.get("supabase_write_count", 0) and cycle.get("mode") == "read_only":
            errors.append(f"cycle {index} wrote during read-only mode")
    return {
        "contract": "renewal_soak_report_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only_aggregate",
        "cycle_count": len(cycles),
        "minimum_cycles": minimum_cycles,
        "ok": not errors,
        "errors": errors,
        "supabase_write_count": 0,
        "telegram_mutation_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate renewal soak cycle reports.")
    parser.add_argument("cycles_file")
    parser.add_argument("--minimum-cycles", type=int, default=4)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.cycles_file, encoding="utf-8") as handle:
        cycles = json.load(handle)
    report = build_soak_report(cycles, minimum_cycles=args.minimum_cycles)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
