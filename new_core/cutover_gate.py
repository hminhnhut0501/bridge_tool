from __future__ import annotations

from dataclasses import dataclass

from .mutation_gate import MutationGate


@dataclass(frozen=True, slots=True)
class CutoverDecision:
    allowed: bool
    reasons: tuple[str, ...]


def evaluate_cutover(
    canary: dict,
    *,
    duplicate_jobs: int = 0,
    missing_group_ids: int = 0,
    gate: MutationGate | None = None,
) -> CutoverDecision:
    gate = gate or MutationGate()
    reasons = []
    actions = canary.get("action_counts") or {}
    if actions.get("REVIEW", 0) > 0:
        reasons.append("canary_review_remaining")
    if actions.get("UNKNOWN", 0) > 0:
        reasons.append("canary_unknown_remaining")
    if duplicate_jobs:
        reasons.append("duplicate_jobs")
    if missing_group_ids:
        reasons.append("missing_group_ids")
    if not gate.allow(1):
        reasons.append("mutation_gate_not_ready")
    return CutoverDecision(not reasons, tuple(reasons))
