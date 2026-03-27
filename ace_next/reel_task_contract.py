from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


VALID_REEL_PRIORITIES = {"low", "medium", "high", "critical"}


@dataclass
class ReelTaskContract:
    ok: bool
    target_format: str
    priority: str
    hook_required: bool
    storyboard_required: bool
    rhythm_required: bool
    subtitles_required: bool
    audio_direction_required: bool
    cinematic_gate_required: bool
    naturalism_required: bool
    creative_inputs: dict[str, Any] = field(default_factory=dict)
    study_mapping: dict[str, Any] = field(default_factory=dict)
    guardrails: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_priority(value: Any) -> str:
    clean = _clean_text(value).lower()
    return clean if clean in VALID_REEL_PRIORITIES else "high"


def build_reel_task_contract(
    *,
    creative_plan: dict[str, Any] | None = None,
    priority: str = "high",
) -> ReelTaskContract:
    plan = dict(creative_plan or {})

    study_mapping = {
        "hook_attention": True,
        "rhythm_engine": True,
        "naturalism": True,
        "audio_direction": True,
        "cinematic_gate": True,
    }

    guardrails = {
        "anti_dead_air": True,
        "anti_plastic_reel": True,
        "require_multimodal_qa": True,
        "require_publish_guard": True,
        "brand_live_allowed": False,
    }

    return ReelTaskContract(
        ok=True,
        target_format="reel",
        priority=_normalize_priority(priority),
        hook_required=True,
        storyboard_required=True,
        rhythm_required=True,
        subtitles_required=True,
        audio_direction_required=True,
        cinematic_gate_required=True,
        naturalism_required=True,
        creative_inputs={
            "headline": plan.get("headline"),
            "hook": plan.get("hook"),
            "body": plan.get("body"),
            "cta": plan.get("cta"),
            "payoff": plan.get("payoff"),
        },
        study_mapping=study_mapping,
        guardrails=guardrails,
        notes=["phase_4_reel_task_contract"],
    )


def reel_task_contract_examples() -> dict[str, Any]:
    return {
        "ok": True,
        "reel": build_reel_task_contract(
            creative_plan={
                "headline": "retenção nasce no primeiro segundo",
                "hook": "se a abertura falha, o resto morre",
                "body": "ritmo, áudio e tensão precisam andar juntos",
                "cta": "salve isso para revisar seu próximo reel",
                "payoff": "clareza prática e aplicável",
            },
            priority="critical",
        ).to_dict(),
    }
