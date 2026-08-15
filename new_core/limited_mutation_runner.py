from __future__ import annotations

from dataclasses import dataclass

from .cutover_gate import CutoverDecision
from .mutation_gate import MutationGate


@dataclass(frozen=True, slots=True)
class LimitedMutationResult:
    status: str
    reason: str
    worker_result: object | None = None


async def run_limited_mutation(
    worker,
    *,
    cutover: CutoverDecision,
    gate: MutationGate,
) -> LimitedMutationResult:
    if not gate.enabled:
        return LimitedMutationResult("DISABLED", "mutation_gate_off")
    if not cutover.allowed:
        return LimitedMutationResult("BLOCKED", ";".join(cutover.reasons))
    if not gate.allow(1):
        return LimitedMutationResult("BLOCKED", "unsafe_mutation_limits")
    result = await worker(limit=gate.limit(gate.max_batch))
    return LimitedMutationResult("EXECUTED", "limited_batch_complete", result)
