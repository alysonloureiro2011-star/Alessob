from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .creative_planner import build_creative_plan
from .mission_control import decide_mission


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        try:
            parsed = value.to_dict()
            return dict(parsed) if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _safe_list_of_dicts(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    safe_items: list[dict[str, Any]] = []
    for item in value:
        parsed = _safe_dict(item)
        if parsed:
            safe_items.append(parsed)
    return safe_items


def _planner_overrides_from_mission_decision(mission_decision: dict[str, Any] | None) -> dict[str, Any]:
    mission_decision = dict(mission_decision or {})
    content_type = str(mission_decision.get("content_type") or "").strip().lower()
    publish_format_now = content_type if content_type in {"image", "carousel", "story", "reel"} else None

    return {
        "strategic_target_format": content_type or None,
        "publish_format_now": publish_format_now,
        "publish_style": None,
        "goal": mission_decision.get("goal"),
        "hypothesis": mission_decision.get("hypothesis"),
        "planner_selected": mission_decision.get("planner_selected"),
    }


@dataclass(frozen=True)
class EditorialBrainRequest:
    trend: str
    format_hint: str | None
    recent_signal_score: float | None
    queue_state: dict[str, Any]
    signal_context: dict[str, Any]
    brand_context: dict[str, Any]
    recent_memory: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EditorialBrainResult:
    ok: bool
    trend: str
    mission_decision: dict[str, Any]
    planner_overrides: dict[str, Any]
    creative_plan: dict[str, Any]
    brain_state: str
    studies_applied: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class EditorialBrainV2:
    """
    Camada soberana do cérebro editorial.

    Função:
    - receber tendência e contexto
    - decidir missão
    - transformar a decisão em overrides
    - gerar o plano criativo final

    Nesta etapa ele não substitui o runtime.
    Ele cria a camada limpa que será plugada nas próximas ondas.
    """

    def build_request(
        self,
        *,
        trend: Any,
        format_hint: Any = None,
        recent_signal_score: float | None = None,
        queue_state: dict[str, Any] | None = None,
        signal_context: dict[str, Any] | None = None,
        brand_context: dict[str, Any] | None = None,
        recent_memory: list[dict[str, Any]] | None = None,
    ) -> EditorialBrainRequest:
        cleaned_trend = _clean_text(trend) or "teste real"
        cleaned_format_hint = _clean_text(format_hint) or None

        return EditorialBrainRequest(
            trend=cleaned_trend,
            format_hint=cleaned_format_hint,
            recent_signal_score=recent_signal_score,
            queue_state=_safe_dict(queue_state),
            signal_context=_safe_dict(signal_context),
            brand_context=_safe_dict(brand_context),
            recent_memory=_safe_list_of_dicts(recent_memory),
        )

    def run(
        self,
        *,
        trend: Any,
        format_hint: Any = None,
        recent_signal_score: float | None = None,
        queue_state: dict[str, Any] | None = None,
        signal_context: dict[str, Any] | None = None,
        brand_context: dict[str, Any] | None = None,
        recent_memory: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        request = self.build_request(
            trend=trend,
            format_hint=format_hint,
            recent_signal_score=recent_signal_score,
            queue_state=queue_state,
            signal_context=signal_context,
            brand_context=brand_context,
            recent_memory=recent_memory,
        )

        mission_decision = decide_mission(
            request.trend,
            format_hint=request.format_hint,
            signal_context=request.signal_context,
            brand_context=request.brand_context,
            queue_state=request.queue_state,
            recent_signal_score=request.recent_signal_score,
        )

        planner_overrides = _planner_overrides_from_mission_decision(mission_decision)

        creative_plan_obj = build_creative_plan(
            request.trend,
            overrides=planner_overrides,
            mission_decision=mission_decision,
            recent_memory=request.recent_memory,
        )
        creative_plan = _safe_dict(creative_plan_obj)

        result = EditorialBrainResult(
            ok=True,
            trend=request.trend,
            mission_decision=mission_decision,
            planner_overrides=planner_overrides,
            creative_plan=creative_plan,
            brain_state="editorial_brain_v2_ready",
            studies_applied=[
                "psicologia_cognitiva_clareza",
                "agentic_workflow_editorial",
                "continuidade_serial",
                "retencao_por_hook_e_payoff",
            ],
        )
        return {
            "request": request.to_dict(),
            **result.to_dict(),
        }


def editorial_brain_v2_examples() -> dict[str, Any]:
    brain = EditorialBrainV2()
    return brain.run(
        trend="clareza, disciplina e direção",
        format_hint="image",
        recent_signal_score=0.62,
        queue_state={"active_jobs": 0, "pending_jobs": 0},
        signal_context={"source": "example"},
        brand_context={"brand_surface_mode": "protected"},
        recent_memory=[],
    )
