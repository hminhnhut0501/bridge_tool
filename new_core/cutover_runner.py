from __future__ import annotations

from dataclasses import dataclass

from .cutover_gate import CutoverDecision


@dataclass(frozen=True, slots=True)
class RunnerResult:
    status: str
    reason: str
    worker_result: object | None = None


async def run_one_batch(
    worker,
    *,
    cutover: CutoverDecision,
    enabled: bool,
    batch_limit: int = 5,
) -> RunnerResult:
    """Run exactly one bounded batch; scheduling is owned by the platform."""
    if not enabled:
        return RunnerResult("DISABLED", "kill_switch_off")
    if not cutover.allowed:
        return RunnerResult("BLOCKED", ";".join(cutover.reasons))
    result = await worker(limit=max(1, min(batch_limit, 5)))
    return RunnerResult("EXECUTED", "one_batch_complete", result)
