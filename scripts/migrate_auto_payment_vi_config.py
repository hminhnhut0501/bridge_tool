"""Copy legacy auto payment config into the new VI namespace.

This script is intentionally conservative:
- dry run by default
- only copies legacy values into missing AUTO_PAYMENT_VI_* keys
- never overwrites existing VI values unless --overwrite is passed
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from database import db  # noqa: E402


MAPPINGS = {
    "AUTO_PAYMENT_NEW_ENABLED": "AUTO_PAYMENT_VI_NEW_ENABLED",
    "AUTO_PAYMENT_NEW_SCHEDULE_ENABLED": "AUTO_PAYMENT_VI_NEW_SCHEDULE_ENABLED",
    "AUTO_PAYMENT_NEW_WINDOWS": "AUTO_PAYMENT_VI_NEW_WINDOWS",
    "AUTO_PAYMENT_RETURNING_ENABLED": "AUTO_PAYMENT_VI_RETURNING_ENABLED",
    "AUTO_PAYMENT_RETURNING_SCHEDULE_ENABLED": "AUTO_PAYMENT_VI_RETURNING_SCHEDULE_ENABLED",
    "AUTO_PAYMENT_RETURNING_WINDOWS": "AUTO_PAYMENT_VI_RETURNING_WINDOWS",
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes back to the active config store.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing VI keys with legacy values.")
    args = parser.parse_args()

    changes = []
    for legacy_key, vi_key in MAPPINGS.items():
        legacy_value = str(db.get_config(legacy_key, "") or "").strip()
        vi_value = str(db.get_config(vi_key, "") or "").strip()
        if not legacy_value:
            continue
        if vi_value and not args.overwrite:
            continue
        changes.append((legacy_key, vi_key, legacy_value, vi_value))

    print(f"Legacy keys scanned: {len(MAPPINGS)}")
    print(f"Planned copies: {len(changes)}")
    for legacy_key, vi_key, legacy_value, vi_value in changes:
        print(f"  {legacy_key} -> {vi_key} | {legacy_value!r} (existing={vi_value!r})")

    if not args.apply:
        print("Dry run only. Add --apply to write values.")
        return

    for _legacy_key, vi_key, legacy_value, _vi_value in changes:
        db.set_config(vi_key, legacy_value)
    print("Migration completed.")


if __name__ == "__main__":
    main()
