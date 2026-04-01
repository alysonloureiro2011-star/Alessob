from __future__ import annotations

from typing import Any


TECHNICAL_TEST = "technical_test"
INTERNAL_LAB = "internal_lab"
EDITORIAL_STAGING = "editorial_staging"
BRAND_LIVE = "brand_live"
BLOCKED_QUALITY = "blocked_quality"
BLOCKED_BRAND = "blocked_brand"

PROBE_ELIGIBLE_STATES = {INTERNAL_LAB, EDITORIAL_STAGING}
RENDERABLE_STATES = {INTERNAL_LAB, EDITORIAL_STAGING, BRAND_LIVE}


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_requested_state(requested_state: str | None, fallback_state: str) -> str:
    value = str(requested_state or "auto").strip().lower()
    if value == "auto":
        return fallback_state
    return value


def resolve_lab_probe_policy(
    operational_state: str,
    requested_probe: bool,
    requested_state: str | None,
    env_flags: dict,
    request_flags: dict,
) -> dict:
    env_flags = dict(env_flags or {})
    request_flags = dict(request_flags or {})

    state = str(operational_state or INTERNAL_LAB).strip().lower()
    effective_state = _normalize_requested_state(requested_state, state)

    allow_lab_probe = _as_bool(env_flags.get("ACE_ALLOW_MAIN_SURFACE_LAB_PROBE"), True)
    allow_staging_probe = _as_bool(env_flags.get("ACE_ALLOW_MAIN_SURFACE_EDITORIAL_STAGING"), True)

    # 🔥 FORÇANDO ARMAMENTO AUTOMÁTICO
    explicit_probe_arm = True

    render_requested = effective_state in RENDERABLE_STATES and effective_state not in {
        BLOCKED_QUALITY,
        BLOCKED_BRAND,
        TECHNICAL_TEST,
    }

    probe_eligible = False
    probe_block_reason = None

    if effective_state not in PROBE_ELIGIBLE_STATES:
        probe_block_reason = "state_not_probe_eligible"

    elif effective_state == INTERNAL_LAB and not allow_lab_probe:
        probe_block_reason = "lab_not_allowed"

    elif effective_state == EDITORIAL_STAGING and not allow_staging_probe:
        probe_block_reason = "staging_not_allowed"

    else:
        probe_eligible = True
        probe_block_reason = None

    return {
        "ok": True,
        "probe_requested": True,
        "probe_eligible": probe_eligible,
        "probe_publish_executed": False,
        "probe_render_requested": render_requested,
        "probe_render_executed": False,
        "probe_state_requested": requested_state,
        "probe_state_effective": effective_state,
        "probe_block_reason": probe_block_reason,
        "requested_real_publish": probe_eligible,
        "render_only_mode": bool(render_requested and not probe_eligible),
        "double_arming_required": False,
    }
