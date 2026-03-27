from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


VALID_VISUAL_TARGETS = {"image", "carousel", "story", "reel_cover"}
VALID_VISUAL_PRIORITIES = {"low", "medium", "high", "critical"}


@dataclass
class VisualTaskContract:
    ok: bool
    target_format: str
    priority: str
    identity_mode: str
    hierarchy_required: bool
    safe_zone_policy: str
    contrast_policy: str
    pattern_interrupt_required: bool
    naturalism_required: bool
    creative_inputs: dict[str, Any] = field(default_factory=dict)
    study_mapping: dict[str, Any] = field(default_factory=dict)
    guardrails: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_target_format(value: Any) -> str:
    clean = _clean_text(value).lower()
    if clean in VALID_VISUAL_TARGETS:
        return clean
    if clean == "reel":
        return "reel_cover"
    return "image"


def _normalize_priority(value: Any) -> str:
    clean = _clean_text(value).lower()
    return clean if clean in VALID_VISUAL_PRIORITIES else "medium"


def build_visual_task_contract(
    *,
    creative_plan: dict[str, Any] | None = None,
    strategic_format: str | None = None,
    priority: str = "medium",
) -> VisualTaskContract:
    plan = dict(creative_plan or {})
    target_format = _normalize_target_format(
        strategic_format or plan.get("publish_format_now") or plan.get("strategic_target_format")
    )
    normalized_priority = _normalize_priority(priority)

    study_mapping = {
        "pattern_interrupt_visual": True,
        "safe_zones": True,
        "visual_hierarchy": True,
        "contrast": True,
        "naturalism": target_format in {"story", "reel_cover"},
    }

    guardrails = {
        "anti_generic_layout": True,
        "anti_commodity_template": True,
        "require_hierarchy_gate": True,
        "require_brand_dignity_check": True,
        "brand_live_allowed": False,
    }

    return VisualTaskContract(
        ok=True,
        target_format=target_format,
        priority=normalized_priority,
        identity_mode="premium_brand_system_v1",
        hierarchy_required=True,
        safe_zone_policy="mobile_first_safe_zones",
        contrast_policy="premium_high_contrast",
        pattern_interrupt_required=True,
        naturalism_required=target_format in {"story", "reel_cover"},
        creative_inputs={
            "headline": plan.get("headline"),
            "hook": plan.get("hook"),
            "body": plan.get("body"),
            "cta": plan.get("cta"),
            "support_points": plan.get("support_points") or [],
        },
        study_mapping=study_mapping,
        guardrails=guardrails,
        notes=["phase_3_visual_task_contract"],
    )


def visual_task_contract_examples() -> dict[str, Any]:
    return {
        "ok": True,
        "image": build_visual_task_contract(
            creative_plan={
                "headline": "clareza vence ruído",
                "hook": "o problema não é falta de informação",
                "body": "é excesso sem hierarquia",
                "cta": "salve para revisar depois",
                "publish_format_now": "image",
            },
            priority="high",
        ).to_dict(),
        "reel_cover": build_visual_task_contract(
            creative_plan={
                "headline": "retenção não nasce no acaso",
                "hook": "ela nasce no primeiro segundo",
                "publish_format_now": "reel",
            },
            priority="critical",
        ).to_dict(),
    }
