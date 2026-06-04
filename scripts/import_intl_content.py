"""Import English bot content from the intl SQLite database into Supabase.

Only *_EN config keys and *_en menu pages are copied. Vietnamese content and
operational data are never modified.
"""

import argparse
import os
import sqlite3

import requests


def upsert(url, key, table, rows, conflict):
    if not rows:
        return
    response = requests.post(
        f"{url.rstrip('/')}/rest/v1/{table}",
        params={"on_conflict": conflict},
        headers={
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
        json=rows,
        timeout=30,
    )
    response.raise_for_status()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sqlite_path")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    connection = sqlite3.connect(args.sqlite_path)
    connection.row_factory = sqlite3.Row
    configs = [
        {"key": row["key"], "value": row["value"] or ""}
        for row in connection.execute("select key, value from bot_config where key like '%_EN'")
    ]
    pages = [
        {
            "page_id": row["page_id"],
            "image_url": row["image_url"] or "",
            "body": row["body"] or "",
            "layout": row["layout"] or "",
        }
        for row in connection.execute(
            "select page_id, image_url, body, layout from menu_pages where page_id like '%_en'"
        )
    ]
    connection.close()

    print(f"English config rows: {len(configs)}")
    print(f"English menu pages: {len(pages)}")
    if args.dry_run:
        return

    url = os.getenv("SUPABASE_URL", "").strip()
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")
    upsert(url, key, "bot_config", configs, "key")
    upsert(url, key, "menu_pages", pages, "page_id")
    print("English content imported successfully.")


if __name__ == "__main__":
    main()
