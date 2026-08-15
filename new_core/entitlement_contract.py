from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


ALLOWED_GROUP_CODES = {
    "COMBO_FULL", "PRIME", "BOY", "REAL", "ASIA", "PINK_SPECIAL",
}
ALLOWED_STATES = {"ACTIVE", "EXPIRED", "CANCELLED", "REVIEW"}


@dataclass(frozen=True, slots=True)
class Entitlement:
    source_order_id: str
    telegram_user_id: str
    group_code: str
    group_id: str | None
    starts_at: datetime | None
    expires_at: datetime | None
    is_lifetime: bool
    state: str
    source_quality: str

    def validate(self) -> None:
        if not self.source_order_id or not self.telegram_user_id:
            raise ValueError("entitlement identity is required")
        if self.group_code not in ALLOWED_GROUP_CODES:
            raise ValueError("unsupported group_code")
        if self.state not in ALLOWED_STATES:
            raise ValueError("unsupported entitlement state")
        if not self.is_lifetime and self.expires_at is None:
            raise ValueError("timed entitlement requires expires_at")


def entitlement_key(value: Entitlement) -> tuple[str, str]:
    value.validate()
    return value.source_order_id, value.group_code
