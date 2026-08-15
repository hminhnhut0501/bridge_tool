from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MutationGate:
    enabled: bool = False
    max_batch: int = 5
    concurrency: int = 1

    def allow(self, requested: int) -> bool:
        return self.enabled and requested > 0 and self.max_batch <= 5 and self.concurrency == 1

    def limit(self, requested: int) -> int:
        return max(0, min(requested, self.max_batch, 5))


def mutation_status(gate: MutationGate) -> dict:
    return {
        "enabled": gate.enabled,
        "max_batch": gate.limit(gate.max_batch),
        "concurrency": gate.concurrency,
        "safe_to_mutate": gate.allow(1),
    }
