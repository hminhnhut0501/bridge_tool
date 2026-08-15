from __future__ import annotations

import argparse
import json

from new_core.cutover_gate import evaluate_cutover
from new_core.mutation_gate import MutationGate


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate limited mutation preflight; no mutation.")
    parser.add_argument("canary_report")
    parser.add_argument("--duplicate-jobs", type=int, default=0)
    parser.add_argument("--missing-group-ids", type=int, default=0)
    args = parser.parse_args()
    with open(args.canary_report, encoding="utf-8") as handle:
        report = json.load(handle)
    decision = evaluate_cutover(
        report,
        duplicate_jobs=args.duplicate_jobs,
        missing_group_ids=args.missing_group_ids,
        gate=MutationGate(enabled=True, max_batch=5, concurrency=1),
    )
    output = {
        "mode": "preflight_only",
        "allowed": decision.allowed,
        "reasons": list(decision.reasons),
        "batch_limit": 5,
        "concurrency": 1,
        "supabase_write_count": 0,
        "telegram_mutation_count": 0,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if decision.allowed else 1


if __name__ == "__main__":
    raise SystemExit(main())
