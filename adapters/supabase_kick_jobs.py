from __future__ import annotations

import json
import urllib.parse
import urllib.request


class SupabaseKickJobAdapter:
    """Production boundary for kick jobs; claiming is delegated to an RPC."""

    def __init__(self, base_url: str, service_key: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
        }

    def claim_due(self, *, before, limit: int) -> list[dict]:
        payload = {"p_before": before.isoformat(), "p_limit": max(1, min(limit, 50))}
        return self._post("/rest/v1/rpc/claim_entitlement_kick_jobs", payload)

    def update(self, job_id: str, payload: dict) -> None:
        query = urllib.parse.urlencode({"id": f"eq.{job_id}"})
        self._request(
            f"/rest/v1/entitlement_kick_jobs?{query}",
            method="PATCH",
            body=payload,
            prefer="return=minimal",
        )

    def _post(self, path: str, payload: dict):
        return self._request(path, method="POST", body=payload)

    def _request(self, path: str, *, method: str, body: dict, prefer: str | None = None):
        headers = dict(self.headers)
        if prefer:
            headers["Prefer"] = prefer
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=json.dumps(body).encode("utf-8"),
            headers=headers,
            method=method,
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            raw = response.read()
            if not raw:
                return []
            return json.loads(raw.decode("utf-8"))
