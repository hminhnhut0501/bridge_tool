"""Copy legacy config keys into the new canonical namespace.

This migration is conservative:
- dry run by default
- copies values from legacy keys into canonical keys
- preserves legacy keys through the alias-aware write path
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config_aliases import canonical_config_key, canonicalize_config_rows  # noqa: E402
from database import db  # noqa: E402
from supabase_store import supabase_store  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes back to Supabase.")
    args = parser.parse_args()

    raw_rows = supabase_store.get_config()
    rows = canonicalize_config_rows(raw_rows)
    raw_by_key = {str(row.get("key") or "").strip().upper(): str(row.get("value") or "").strip() for row in raw_rows or []}

    changes = []
    for row in rows:
        canonical_key = canonical_config_key(row.get("key"))
        canonical_value = str(row.get("value") or "").strip()
        if not canonical_key or not canonical_value:
            continue
        existing = raw_by_key.get(canonical_key, "")
        if existing == canonical_value:
            continue
        changes.append((canonical_key, canonical_value, existing))

    print(f"Canonical keys scanned: {len(rows)}")
    print(f"Planned copies: {len(changes)}")
    for canonical_key, canonical_value, existing in changes:
        print(f"  {canonical_key} <- {canonical_value!r} (existing={existing!r})")

    if not args.apply:
        print("Dry run only. Add --apply to write values.")
        return

    for canonical_key, canonical_value, _existing in changes:
        db.set_config(canonical_key, canonical_value)
    print("Migration completed.")


if __name__ == "__main__":
    main()
