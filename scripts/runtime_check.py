from __future__ import annotations

import importlib.util
import argparse
import json
import os
import sys


REQUIRED_KEYS = ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY", "BOT_TOKEN")


def check_runtime() -> dict[str, object]:
    missing = [key for key in REQUIRED_KEYS if not os.getenv(key)]
    requests_available = importlib.util.find_spec("requests") is not None
    return {
        "ok": not missing and requests_available,
        "missing_env": missing,
        "requests_available": requests_available,
        "python": sys.version.split()[0],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate runtime dependencies and required environment.")
    parser.add_argument("--env-file", help="Load variables from a dotenv file before checking.")
    args = parser.parse_args()
    if args.env_file:
        from dotenv import load_dotenv

        load_dotenv(args.env_file, override=False)
    report = check_runtime()
    print(json.dumps(report, indent=2, sort_keys=True))
    raise SystemExit(0 if report["ok"] else 1)
