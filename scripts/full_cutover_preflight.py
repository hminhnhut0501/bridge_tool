from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from new_core.observability import dynamic_cutover_gate


def build_preflight(config: dict, health: dict) -> dict:
    static_errors = []
    required = {
        "RENEWAL_NEW_CORE_FULL_CUTOVER": "ON",
        "RENEWAL_NEW_CORE_DRY_RUN": "OFF",
        "RENEWAL_NEW_CORE_LIMITED_MUTATION": "OFF",
        "RENEWAL_NEW_CORE_CUTOVER_ACK": "I_UNDERSTAND",
    }
    for key, expected in required.items():
        if str(config.get(key) or "").strip().upper() != expected:
            static_errors.append(f"{key} must be {expected}")
    health_ok, health_errors = dynamic_cutover_gate(health)
    errors = static_errors + health_errors
    return {
        "contract": "renewal_full_cutover_preflight_v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "preflight",
        "ok": not errors,
        "errors": errors,
        "static_config": config,
        "health": health,
        "supabase_write_count": 0,
        "telegram_mutation_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate full renewal worker cutover without enabling it.")
    parser.add_argument("config_file")
    parser.add_argument("health_file")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.config_file, encoding="utf-8") as handle:
        config = json.load(handle)
    with open(args.health_file, encoding="utf-8") as handle:
        health = json.load(handle)
    report = build_preflight(config, health)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
