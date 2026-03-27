from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


VALID_EDITORIAL_TASK_TYPES = {
    "hook",
    "headline",
    "caption",
    "script",
    "planner",
    "editorial",
    "continuity",
    "distribution",
}

VALID_PRIORITY_LEVELS = {"low", "medium", "high", "critical"}
VALID_TARGET_FORMATS = {"image", "carousel", "story", "reel"}


@dataclass
class EditorialTaskContract:
    ok: bool
    task_type: str
    topic_seed: str
    objective: str
    target_format: str
    priority: str
    hypothesis: str | None = None
    continuity_required: bool = False
    serial_context: dict[str, Any] = field(default_factory=dict)
    distribution_context: dict[str, Any] = field(default_factory=dict)
    study_mapping: dict[str, Any] = field(default_factory=dict)
    guardrails: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _valid_or_default(value: str, allowed: set[str], default: str) -> str:
    cleaned = _clean_text(value).lower()
    return cleaned if cleaned in allowed else default


def build_editorial_task_contract(
    *,
    task_type: str,
    topic_seed: str,
    objective: str,
    target_format: str,
    priority: str = "medium",
    hypothesis: str | None = None,
    continuity_required: bool = False,
    serial_context: dict[str, Any] | None = None,
    distribution_context: dict[str, Any] | None = None,
    notes: list[str] | None = None,
) -> EditorialTaskContract:
    clean_task_type = _valid_or_default(task_type, VALID_EDITORIAL_TASK_TYPES, "planner")
    clean_topic_seed = _clean_text(topic_seed) or "clareza, disciplina e direção"
    clean_objective = _clean_text(objective) or "entregar peça editorial premium"
    clean_target_format = _valid_or_default(target_format, VALID_TARGET_FORMATS, "image")
    clean_priority = _valid_or_default(priority, VALID_PRIORITY_LEVELS, "medium")

    study_mapping = {
        "clt_density_control": clean_task_type in {"planner", "headline", "caption", "script"},
        "narrative_steps": clean_task_type in {"planner", "script", "continuity"},
        "attention_engineering": clean_task_type in {"hook", "headline", "caption", "distribution"},
        "serial_continuity": bool(continuity_required),
    }

    guardrails = {
        "anti_cliche_required": True,
        "anti_commodity_required": True,
        "requires_human_review_for_brand_live": True,
        "brand_live_allowed": False,
        "runtime_is_thin_shell": True,
    }

    return EditorialTaskContract(
        ok=True,
        task_type=clean_task_type,
        topic_seed=clean_topic_seed,
        objective=clean_objective,
        target_format=clean_target_format,
        priority=clean_priority,
        hypothesis=_clean_text(hypothesis) or None,
        continuity_required=bool(continuity_required),
        serial_context=dict(serial_context or {}),
        distribution_context=dict(distribution_context or {}),
        study_mapping=study_mapping,
        guardrails=guardrails,
        notes=list(notes or []),
    )


def editorial_task_contract_examples() -> dict[str, Any]:
    return {
        "ok": True,
        "planner": build_editorial_task_contract(
            task_type="planner",
            topic_seed="clareza, disciplina e direção",
            objective="definir peça premium com hook, headline, payoff e CTA",
            target_format="reel",
            priority="high",
            hypothesis="hook_de_curiosidade_com_payoff_concreto_melhora_retenção",
            continuity_required=True,
            serial_context={"series_name": "Liberta a Verdade"},
            distribution_context={"timing_hypothesis": "24-48h"},
            notes=["phase_2_sovereign_editorial_brain"],
        ).to_dict(),
        "caption": build_editorial_task_contract(
            task_type="caption",
            topic_seed="prosperidade com disciplina",
            objective="gerar legenda premium anti-clichê",
            target_format="carousel",
            priority="medium",
            continuity_required=False,
        ).to_dict(),
    }
