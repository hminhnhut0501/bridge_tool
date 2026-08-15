from __future__ import annotations

import argparse
import json
import os
import re
import unicodedata
from collections import Counter

from scripts.production_renewal_snapshot import read_all


def clean(value: str) -> str:
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text.replace("đ", "d").replace("Đ", "D")).strip().lower()


def canonical_plan_name(value: str) -> tuple[str | None, str]:
    raw = str(value or "").strip()
    text = clean(raw)
    lifetime = bool(re.search(r"tron doi|lifetime|vinh vien", text))
    duration = "Trọn Đời" if lifetime else "30 Ngày"
    # Hidden plans retain their exact token/name until reviewed separately.
    if "pink" in text or "hidden" in text or "hg:" in text:
        return None, "hidden_review"
    if any(token in text for token in ("all access", "allaccess", "svip", "combo", "full 4", "full4")):
        return f"Combo {duration}", "combo_alias"
    if "prime" in text:
        return f"Prime {duration}", "prime"
    if "boy" in text:
        return f"Boy {duration}", "boy"
    if "black" in text or re.search(r"\breal\b", text):
        return f"Real {duration}", "real_alias"
    if "asia" in text:
        return f"Asia {duration}", "asia"
    return None, "unmapped"


def canonical_duration(value: str) -> str:
    text = clean(value)
    if re.search(r"tron doi|lifetime|vinh vien", text):
        return "LIFETIME"
    day_match = re.search(r"(\d+)\s*(ngay|day|days)\b", text)
    if day_match:
        return f"DAYS:{int(day_match.group(1))}"
    month_match = re.search(r"(\d+)\s*(thang|month|months)\b", text)
    if month_match:
        return f"MONTHS:{int(month_match.group(1))}"
    year_match = re.search(r"(\d+)\s*(nam|year|years)\b", text)
    if year_match:
        return f"YEARS:{int(year_match.group(1))}"
    if any(token in text for token in ("prime", "boy", "real", "black", "asia", "combo", "svip", "all access", "allaccess")):
        return "CUSTOM"
    return "REVIEW"


def build_report(rows: list[dict], *, source: str) -> dict:
    changes = []
    reasons = Counter()
    for row in rows:
        old = str(row.get("plan_name") or "").strip()
        new, reason = canonical_plan_name(old)
        duration = canonical_duration(old)
        reasons[reason] += 1
        if new and new != old:
            changes.append({"id": row.get("order_id") or row.get("id"), "old": old, "new": new, "canonical_duration": duration, "reason": reason})
    return {
        "contract": "canonical_plan_names_v1",
        "mode": "dry_run",
        "source": source,
        "rows": len(rows),
        "changes": changes,
        "reason_counts": dict(reasons),
        "unmapped_or_review": [row for row in rows if not canonical_plan_name(str(row.get("plan_name") or ""))[0]],
        "write_count": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan canonical renewal plan names; dry-run by default.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--apply", action="store_true", help="Reserved; requires an explicit migration implementation review.")
    args = parser.parse_args()
    if args.apply:
        raise SystemExit("Refusing direct apply: review the dry-run and schema backup first.")
    base_url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not base_url or not key:
        raise SystemExit("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    orders = read_all(base_url, key, "orders", {"select": "order_id,plan_name,status,expire_at,telegram_user_id"})
    tasks = read_all(base_url, key, "renewal_kick_tasks_v2", {"select": "id,order_id,plan_name,task_state"})
    report = {
        "orders": build_report(orders, source="orders"),
        "tasks": build_report(tasks, source="renewal_kick_tasks_v2"),
        "write_count": 0,
    }
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    print(json.dumps({"orders": report["orders"]["rows"], "order_changes": len(report["orders"]["changes"]), "task_changes": len(report["tasks"]["changes"]), "write_count": 0}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
