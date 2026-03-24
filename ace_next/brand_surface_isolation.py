from __future__ import annotations

from typing import Any


TECHNICAL_TEST = "technical_test"
INTERNAL_LAB = "internal_lab"
EDITORIAL_STAGING = "editorial_staging"
BRAND_LIVE = "brand_live"
BLOCKED_QUALITY = "blocked_quality"
BLOCKED_BRAND = "blocked_brand"


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def resolve_brand_surface_policy(
    operational_state: str,
    requested_real_publish: bool,
    env_flags: dict,
    request_flags: dict,
    quality_context: dict | None = None,
) -> dict:
    state = str(operational_state or TECHNICAL_TEST).strip().lower()
    env_flags = dict(env_flags or {})
    request_flags = dict(request_flags or {})
    quality_context = dict(quality_context or {})

    surface_mode = str(env_flags.get("ACE_BRAND_SURFACE_MODE") or "protected").strip().lower()
    if surface_mode not in {"protected", "armed"}:
        surface_mode = "protected"

    allow_lab_probe = _as_bool(env_flags.get("ACE_ALLOW_MAIN_SURFACE_LAB_PROBE"), False)
    allow_staging_probe = _as_bool(env_flags.get("ACE_ALLOW_MAIN_SURFACE_EDITORIAL_STAGING"), False)
    require_human_review = _as_bool(env_flags.get("ACE_REQUIRE_HUMAN_REVIEW_FOR_BRAND_LIVE"), True)

    explicit_main_surface_publish = _as_bool(request_flags.get("explicit_main_surface_publish"), False)
    human_review_approved = _as_bool(request_flags.get("human_review_approved"), False)

    result = {
        "ok": True,
        "surface_mode": surface_mode,
        "operational_state": state,
        "main_surface_allowed": False,
        "blocked": True,
        "block_reason": "surface_protected_by_default",
        "requires_explicit_arming": True,
        "requires_brand_live": True,
        "requires_human_review": require_human_review,
        "quality_context": {
            "brand_live_candidate": bool(quality_context.get("brand_live_candidate")),
            "can_publish_real": bool(quality_context.get("can_publish_real")),
        },
    }

    if state == TECHNICAL_TEST:
        result["block_reason"] = "technical_test_never_touches_main_surface"
        return result

    if state == BLOCKED_QUALITY:
        result["block_reason"] = "blocked_quality_cannot_touch_main_surface"
        return result

    if state == BLOCKED_BRAND:
        result["block_reason"] = "blocked_brand_cannot_touch_main_surface"
        return result

    if state == INTERNAL_LAB:
        if requested_real_publish and allow_lab_probe and explicit_main_surface_publish:
            result.update(
                {
                    "surface_mode": "lab_probe_armed",
                    "main_surface_allowed": True,
                    "blocked": False,
                    "block_reason": None,
                    "requires_brand_live": False,
                }
            )
            return result

        result["block_reason"] = "internal_lab_cannot_touch_main_surface"
        return result

    if state == EDITORIAL_STAGING:
        if requested_real_publish and allow_staging_probe and explicit_main_surface_publish:
            result.update(
                {
                    "surface_mode": "editorial_staging_probe_armed",
                    "main_surface_allowed": True,
                    "blocked": False,
                    "block_reason": None,
                    "requires_brand_live": False,
                }
            )
            return result

        result["block_reason"] = "editorial_staging_cannot_touch_main_surface"
        return result

    if state == BRAND_LIVE:
        if not explicit_main_surface_publish:
            result["block_reason"] = "brand_live_not_explicitly_armed"
            return result

        if require_human_review and not human_review_approved:
            result["block_reason"] = "brand_live_requires_human_review"
            return result

        result.update(
            {
                "surface_mode": "brand_live_armed",
                "main_surface_allowed": True,
                "blocked": False,
                "block_reason": None,
                "requires_brand_live": False,
            }
        )
        return result

    result["block_reason"] = "unknown_operational_state"
    return result
