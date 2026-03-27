from __future__ import annotations

from typing import Any

from .runtime_contracts import safe_dict
from .visual_task_contract import build_visual_task_contract
from .visual_premium_bridge import build_visual_premium_bridge


def build_visual_execution_bundle(
    *,
    creative_plan: dict[str, Any] | None = None,
    visual_identity: dict[str, Any] | None = None,
    visual_contract: dict[str, Any] | None = None,
    strategic_format: str | None = None,
    priority: str = "medium",
    capture_mode: str = "safe",
) -> dict[str, Any]:
    plan = safe_dict(creative_plan)

    task_contract = build_visual_task_contract(
        creative_plan=plan,
        strategic_format=strategic_format,
        priority=priority,
    )
    task_dict = task_contract.to_dict() if hasattr(task_contract, "to_dict") else safe_dict(task_contract)

    target_format = (
        strategic_format
        or task_dict.get("target_format")
        or plan.get("publish_format_now")
        or plan.get("strategic_target_format")
        or "image"
    )

    premium_visual = build_visual_premium_bridge(
        creative_plan=plan,
        visual_identity=visual_identity,
        visual_contract=visual_contract,
        strategic_format=str(target_format),
        template_id=None,
        capture_mode=capture_mode,
    )
    premium_dict = safe_dict(premium_visual)

    hierarchy_gate = safe_dict(premium_dict.get("hierarchy_gate"))
    brand_dignity = safe_dict(premium_dict.get("brand_dignity_score"))

    return {
        "ok": True,
        "visual_task_contract": task_dict,
        "visual_task_state": "phase_3_visual_execution_bridge_ready",
        "target_format": task_dict.get("target_format"),
        "priority": task_dict.get("priority"),
        "premium_visual": premium_dict,
        "hierarchy_gate": hierarchy_gate,
        "brand_dignity_score": brand_dignity,
        "approved_for_premium_visual": bool(premium_dict.get("approved_for_premium_visual")),
        "selected_template_id": premium_dict.get("selected_template_id"),
        "premium_render_state": premium_dict.get("premium_render_state"),
        "hardening_applied": premium_dict.get("hardening_applied"),
        "hardening_report": premium_dict.get("hardening_report"),
        "study_alignment": {
            "pattern_interrupt_visual": True,
            "safe_zones": True,
            "contrast": True,
            "visual_hierarchy": True,
            "naturalism": bool(task_dict.get("naturalism_required")),
        },
    }


def visual_execution_bridge_examples() -> dict[str, Any]:
    return {
        "ok": True,
        "image": build_visual_execution_bundle(
            creative_plan={
                "headline": "clareza vence ruído",
                "hook": "o problema não é falta de informação",
                "body": "é excesso sem hierarquia",
                "cta": "salve para revisar depois",
                "publish_format_now": "image",
            },
            priority="high",
        ),
        "reel_cover": build_visual_execution_bundle(
            creative_plan={
                "headline": "retenção nasce no primeiro segundo",
                "hook": "não no acaso",
                "publish_format_now": "reel",
            },
            priority="critical",
        ),
    }
