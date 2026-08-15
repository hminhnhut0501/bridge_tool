from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone


def canary_config() -> dict[str, str]:
    return {
        "canary": os.getenv("RENEWAL_NEW_CORE_CANARY", "OFF"),
        "dry_run": os.getenv("RENEWAL_NEW_CORE_DRY_RUN", "OFF"),
        "limited_mutation": os.getenv("RENEWAL_NEW_CORE_LIMITED_MUTATION", "OFF"),
        "full_cutover": os.getenv("RENEWAL_NEW_CORE_FULL_CUTOVER", "OFF"),
        "mutation_freeze": os.getenv("RENEWAL_MUTATION_FREEZE", "ON"),
    }


def validate_config(config: dict[str, str]) -> list[str]:
    errors = []
    if str(config.get("canary", "")).upper() not in {"ON", "TRUE", "1", "YES"}:
        errors.append("RENEWAL_NEW_CORE_CANARY must be ON")
    if str(config.get("dry_run", "")).upper() not in {"ON", "TRUE", "1", "YES"}:
        errors.append("RENEWAL_NEW_CORE_DRY_RUN must be ON")
    for key in ("limited_mutation", "full_cutover"):
        if str(config.get(key, "")).upper() in {"ON", "TRUE", "1", "YES"}:
            errors.append(f"{key} must be OFF")
    return errors


def validate_result(result: dict) -> list[str]:
    errors = []
    if result.get("mode") != "read_only":
        errors.append("result mode must be read_only")
    if result.get("supabase_write_count") != 0:
        errors.append("supabase_write_count must be 0")
    if result.get("telegram_mutation_count") != 0:
        errors.append("telegram_mutation_count must be 0")
    return errors


async def run_once():
    config = canary_config()
    errors = validate_config(config)
    if errors:
        return {"mode": "blocked", "config": config, "errors": errors}
    import scheduler

    result = await scheduler.run_new_core_cycle()
    report = {
        "mode": "read_only_canary",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "result": result,
    }
    result_dict = result if isinstance(result, dict) else {}
    report["errors"] = validate_result(result_dict)
    report["ok"] = not report["errors"]
    return report


def main() -> int:
    try:
        report = asyncio.run(run_once())
    except Exception as exc:
        report = {"mode": "error", "ok": False, "errors": [f"{type(exc).__name__}: {exc}"]}
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True, default=str))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
