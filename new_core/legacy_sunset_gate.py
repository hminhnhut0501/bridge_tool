from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SunsetDecision:
    allowed: bool
    reasons: tuple[str, ...]


def evaluate_sunset(
    *,
    observation_cycles: int,
    incorrect_kicks: int = 0,
    unresolved_reviews: int = 0,
    legacy_mutations: int = 0,
    data_loss_events: int = 0,
    minimum_cycles: int = 3,
) -> SunsetDecision:
    reasons = []
    if observation_cycles < minimum_cycles:
        reasons.append("observation_window_incomplete")
    if incorrect_kicks:
        reasons.append("incorrect_kicks_detected")
    if unresolved_reviews:
        reasons.append("unresolved_reviews")
    if legacy_mutations:
        reasons.append("legacy_mutation_still_active")
    if data_loss_events:
        reasons.append("data_loss_detected")
    return SunsetDecision(not reasons, tuple(reasons))
