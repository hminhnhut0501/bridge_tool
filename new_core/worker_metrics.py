from __future__ import annotations

from dataclasses import dataclass, field


METRIC_NAMES = (
    "jobs_due", "jobs_claimed", "jobs_done", "jobs_retained", "jobs_review",
    "jobs_retry", "membership_unknown", "telegram_rate_limit", "duplicate_jobs",
)


@dataclass
class WorkerMetrics:
    values: dict[str, int] = field(default_factory=lambda: {name: 0 for name in METRIC_NAMES})

    def increment(self, name: str, amount: int = 1) -> None:
        if name not in self.values:
            raise ValueError(f"unknown worker metric: {name}")
        self.values[name] += amount

    def snapshot(self) -> dict[str, int]:
        return dict(self.values)


def metrics_safe_to_cutover(metrics: dict[str, int]) -> bool:
    return all(metrics.get(name, 0) == 0 for name in ("duplicate_jobs", "telegram_rate_limit"))
