from __future__ import annotations

import asyncio
import json
import os
from datetime import datetime, timezone


def limited_config() -> dict[str, str]:
    return {
        "canary": os.getenv("RENEWAL_NEW_CORE_CANARY", "OFF"),
        "dry_run": os.getenv("RENEWAL_NEW_CORE_DRY_RUN", "ON"),
        "limited_mutation": os.getenv("RENEWAL_NEW_CORE_LIMITED_MUTATION", "OFF"),
        "full_cutover": os.getenv("RENEWAL_NEW_CORE_FULL_CUTOVER", "OFF"),
        "ack": os.getenv("RENEWAL_LIMITED_MUTATION_ACK", ""),
        "mutation_freeze": os.getenv("RENEWAL_MUTATION_FREEZE", "ON"),
        "cohort_user_ids": os.getenv("RENEWAL_NEW_CORE_COHORT_USER_IDS", ""),
        "cohort_order_ids": os.getenv("RENEWAL_NEW_CORE_COHORT_ORDER_IDS", ""),
    }


def validate_config(config: dict[str, str]) -> list[str]:
    errors = []
    if str(config.get("canary", "")).upper() not in {"ON", "TRUE", "1", "YES"}:
        errors.append("canary must be ON")
    if str(config.get("dry_run", "")).upper() in {"ON", "TRUE", "1", "YES"}:
        errors.append("dry_run must be OFF")
    if str(config.get("limited_mutation", "")).upper() not in {"ON", "TRUE", "1", "YES"}:
        errors.append("limited_mutation must be ON")
    if str(config.get("full_cutover", "")).upper() in {"ON", "TRUE", "1", "YES"}:
        errors.append("full_cutover must be OFF")
    if config.get("ack") != "I_UNDERSTAND_LIMITED_MUTATION":
        errors.append("limited mutation acknowledgement is required")
    if str(config.get("mutation_freeze", "ON")).upper() in {"ON", "TRUE", "1", "YES"}:
        errors.append("RENEWAL_MUTATION_FREEZE must be OFF for mutation")
    if not str(config.get("cohort_user_ids") or "").strip() and not str(config.get("cohort_order_ids") or "").strip():
        errors.append("a non-empty user or order cohort is required")
    return errors


async def run_once():
    config = limited_config()
    errors = validate_config(config)
    if errors:
        return {"mode": "blocked", "config": config, "errors": errors}
    import scheduler

    result = await scheduler.run_new_core_cycle()
    return {
        "mode": "limited_mutation",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "result": result,
        "warning": "Review every result before expanding the cohort.",
    }


def main() -> int:
    try:
        report = asyncio.run(run_once())
    except Exception as exc:
        report = {"mode": "error", "errors": [f"{type(exc).__name__}: {exc}"]}
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    return 0 if report.get("mode") == "limited_mutation" else 1


if __name__ == "__main__":
    raise SystemExit(main())
