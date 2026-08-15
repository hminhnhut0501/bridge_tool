from __future__ import annotations


ENTITLEMENT_SOURCE = "customer_entitlements_v2"
KICK_JOB_SOURCE = "entitlement_kick_jobs"
LEGACY_MODE = "READ_ONLY"

ALLOWED_ENTITLEMENT_STATES = frozenset({"ACTIVE", "EXPIRED", "CANCELLED", "REVIEW"})
ALLOWED_JOB_STATES = frozenset({"PENDING", "PROCESSING", "DONE", "RETAINED", "SKIPPED", "RETRY", "REVIEW"})


def assert_scope_contract() -> None:
    if ENTITLEMENT_SOURCE != "customer_entitlements_v2":
        raise AssertionError("entitlement source changed without scope review")
    if KICK_JOB_SOURCE != "entitlement_kick_jobs":
        raise AssertionError("kick job source changed without scope review")
    if LEGACY_MODE != "READ_ONLY":
        raise AssertionError("legacy mutation is outside the frozen scope")
