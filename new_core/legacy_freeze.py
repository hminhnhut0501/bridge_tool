from __future__ import annotations


def legacy_mutation_allowed(*, cutover_enabled: bool, explicit_override: bool = False) -> bool:
    """Legacy mutation is closed once the new worker is cut over."""
    if cutover_enabled:
        return False
    return bool(explicit_override)


def legacy_mode(*, cutover_enabled: bool) -> str:
    return "READ_ONLY" if cutover_enabled else "PRE_CUTOVER"
