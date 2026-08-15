from __future__ import annotations

import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict

from scripts.production_renewal_snapshot import read_all


def normalize(value):
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"[^a-z0-9]+", " ", text.lower().replace("đ", "d")).strip()


def tokens(value):
    ignored = {"vip", "svip", "full", "goi", "nhom", "group", "ngay", "thang", "tron", "doi", "prive", "plus", "premium", "signature", "hang", "cu"}
    return [item for item in normalize(value).split() if item and item not in ignored and not item.isdigit()]


def build_group_map(config_rows, plan_names):
    config = {str(row.get("key") or ""): str(row.get("value") or "") for row in config_rows}
    try:
        group_count = max(1, min(100, int(float(config.get("GROUP_COUNT") or 20))))
    except ValueError:
        group_count = 20
    mapping = {}
    for plan in sorted(set(str(value or "") for value in plan_names)):
        upper = plan.upper()
        matched = []
        for number in range(1, group_count + 1):
            button = config.get(f"BTN_G{number}") or f"Nhóm {number}"
            aliases = re.split(r"[\n,;|]+", config.get(f"BTN_G{number}_ALIASES") or "")
            if any(
                token in upper for token in ("COMBO", "FULL", "SVIP", "ALL ACCESS", "ALLACCESS")
            ) or f"G{number}" in upper:
                matched.append((number, config.get(f"ID_G{number}") or ""))
                continue
            plan_text = normalize(plan)
            button_text = normalize(button)
            alias_text = [normalize(item) for item in aliases if normalize(item)]
            if (button_text and (button_text in plan_text or plan_text in button_text)) or any(item in plan_text or plan_text in item for item in alias_text):
                matched.append((number, config.get(f"ID_G{number}") or ""))
                continue
            plan_tokens = set(tokens(plan))
            button_tokens = set(tokens(button))
            if (button_tokens and button_tokens.issubset(plan_tokens)) or (plan_tokens and plan_tokens.issubset(button_tokens)):
                matched.append((number, config.get(f"ID_G{number}") or ""))
        mapping[plan] = [group_id for _number, group_id in matched if group_id]
    return mapping


def build_report(config_rows, orders, tasks):
    mapping = build_group_map(config_rows, [row.get("plan_name") for row in orders])
    task_plan_names = {str(row.get("plan_name") or "") for row in tasks}
    unavailable = sum(1 for plan in task_plan_names if not mapping.get(plan))
    return {
        "plans": len(mapping),
        "mapped_plans": sum(1 for groups in mapping.values() if groups),
        "unmapped_plans": unavailable,
        "group_count": sum(len(groups) for groups in mapping.values()),
        "task_plan_names": len(task_plan_names),
        "task_plans_unmapped": sum(1 for plan in task_plan_names if not mapping.get(plan)),
        "mapping_by_plan": mapping,
        "write_count": 0,
    }


def main():
    base_url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not base_url or not key:
        print("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required", file=sys.stderr)
        return 2
    try:
        configs = read_all(base_url, key, "bot_config", {"select": "key,value"})
        orders = read_all(base_url, key, "orders", {"select": "plan_name,status"})
        tasks = read_all(base_url, key, "renewal_kick_tasks_v2", {"select": "plan_name"})
        report = build_report(configs, orders, tasks)
        report.pop("mapping_by_plan", None)
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    except Exception as exc:
        print(f"production plan mapping failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
