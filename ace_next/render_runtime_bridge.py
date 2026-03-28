from __future__ import annotations

from pathlib import Path
from typing import Any

from .visual_foundation_pack import render_visual_foundation_card as legacy_render_visual_foundation_card
from .visual_premium_bridge import build_visual_premium_bridge


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _existing_path(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    path = Path(text)
    return str(path) if path.exists() else None


def _premium_asset_path(bundle: dict[str, Any]) -> str | None:
    render = _safe_dict(bundle.get("render"))
    for key in ("screenshot_path",):
        existing = _existing_path(render.get(key))
        if existing:
            return existing
    return None


def render_visual_foundation_card(
    *,
    config: Any,
    plan: dict,
    identity: dict | None = None,
    typography: dict | None = None,
) -> str:
    plan = _safe_dict(plan)
    identity = _safe_dict(identity)
    strategic_format = str(
        plan.get("publish_format_now")
        or plan.get("strategic_target_format")
        or plan.get("format_recommendation")
        or "image"
    ).strip().lower()

    try:
        premium_bundle = build_visual_premium_bridge(
            creative_plan=plan,
            visual_identity=identity,
            visual_contract=None,
            strategic_format=strategic_format,
            capture_mode="safe",
        )
        premium_asset_path = _premium_asset_path(premium_bundle)
        if premium_asset_path:
            return premium_asset_path
    except Exception:
        pass

    return legacy_render_visual_foundation_card(
        config=config,
        plan=plan,
        identity=identity if identity else None,
        typography=typography if typography else None,
    )
