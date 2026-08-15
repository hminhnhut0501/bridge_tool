from __future__ import annotations

import json
import time
import urllib.error
import urllib.request


class ReadonlyHttpError(RuntimeError):
    pass


def get_json(url: str, *, headers: dict[str, str] | None = None, timeout: float = 20, retries: int = 2, backoff: float = 0.4):
    last_error = None
    for attempt in range(retries + 1):
        try:
            request = urllib.request.Request(url, headers=headers or {}, method="GET")
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(backoff * (2 ** attempt))
    raise ReadonlyHttpError(f"GET failed after {retries + 1} attempts: {last_error}") from last_error
