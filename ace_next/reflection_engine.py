from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


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


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _performance_state(real_metrics: dict[str, Any], recommendation: dict[str, Any]) -> str:
    source_status = str(real_metrics.get("source_status") or "")
    recommended_action = str(recommendation.get("recommended_action") or "")

    if source_status == "collected":
        return "measured"
    if recommended_action == "repeat_probe":
        return "collecting_more_signal"
    if source_status in {"not_available_yet", "not_supported_for_content_type"}:
        return "waiting_for_evidence"
    return "reflection_conservative"


def _build_insight(
    *,
    creative_plan: dict[str, Any],
    real_metrics: dict[str, Any],
    recommendation: dict[str, Any],
) -> str:
    topic_seed = _clean_text(creative_plan.get("topic_seed") or creative_plan.get("headline") or "tema atual")
    recommended_action = _clean_text(recommendation.get("recommended_action") or "observar")
    source_status = _clean_text(real_metrics.get("source_status") or "sem leitura real")

    return (
        f"O ciclo atual de {topic_seed} terminou em estado {source_status}. "
        f"A próxima ação sugerida é {recommended_action}."
    )


def _build_next_hypothesis(
    *,
    creative_plan: dict[str, Any],
    recommendation: dict[str, Any],
) -> str:
    format_now = _clean_text(
        creative_plan.get("publish_format_now")
        or creative_plan.get("format_recommendation")
        or "image"
    )
    recommended_action = _clean_text(recommendation.get("recommended_action") or "observe")

    return f"Se o próximo ciclo mantiver {format_now} com ajuste orientado por {recommended_action}, o ACE deve ganhar leitura melhor do sinal."


def _build_guardrails() -> dict[str, Any]:
    return {
        "can_change_brand_policy": False,
        "can_change_editorial_policy": False,
        "can_change_visual_policy": False,
        "can_authorize_brand_live": False,
        "can_autopublish": False,
        "mode": "reflection_only",
    }


@dataclass(frozen=True)
class ReflectionEngineResult:
    ok: bool
    reflection_state: str
    performance_state: str
    insight: str
    next_hypothesis: str
    recommended_action: str
    confidence_hint: str
    reflection_notes: list[str]
    guardrails: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReflectionEngine:
    """
    Camada de reflexão soberana.

    Função:
    - ler o resultado do ciclo
    - consolidar um insight simples
    - gerar hipótese conservadora para o próximo ciclo
    - manter travas duras para não virar autonomia perigosa

    Nesta etapa ele só reflete.
    Não muda política, não publica e não altera a marca.
    """

    def run(
        self,
        *,
        creative_plan: dict[str, Any] | None = None,
        real_metrics: dict[str, Any] | None = None,
        recommendation_engine: dict[str, Any] | None = None,
        attention_metrics: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        creative_plan = _safe_dict(creative_plan)
        real_metrics = _safe_dict(real_metrics)
        recommendation_engine = _safe_dict(recommendation_engine)
        attention_metrics = _safe_dict(attention_metrics)

        performance_state = _performance_state(real_metrics, recommendation_engine)
        insight = _build_insight(
            creative_plan=creative_plan,
            real_metrics=real_metrics,
            recommendation=recommendation_engine,
        )
        next_hypothesis = _build_next_hypothesis(
            creative_plan=creative_plan,
            recommendation=recommendation_engine,
        )

        attention_score = _safe_float(
            (_safe_dict(attention_metrics.get("breakdown"))).get("attention_score")
        )

        if attention_score is None:
            confidence_hint = "low"
        elif attention_score >= 7.5:
            confidence_hint = "medium"
        else:
            confidence_hint = "low"

        recommended_action = _clean_text(
            recommendation_engine.get("recommended_action") or "observe"
        )

        notes = [
            f"performance_state={performance_state}",
            f"recommended_action={recommended_action}",
            "reflection_mode=conservative",
            "brand_policy_locked=true",
        ]

        result = ReflectionEngineResult(
            ok=True,
            reflection_state="reflection_engine_ready",
            performance_state=performance_state,
            insight=insight,
            next_hypothesis=next_hypothesis,
            recommended_action=recommended_action,
            confidence_hint=confidence_hint,
            reflection_notes=notes,
            guardrails=_build_guardrails(),
        )
        return result.to_dict()


def reflection_engine_examples() -> dict[str, Any]:
    engine = ReflectionEngine()
    return engine.run(
        creative_plan={
            "topic_seed": "clareza, disciplina e direção",
            "publish_format_now": "image",
        },
        real_metrics={
            "source_status": "not_available_yet",
        },
        recommendation_engine={
            "recommended_action": "repeat_probe",
        },
        attention_metrics={
            "breakdown": {
                "attention_score": None,
            }
        },
    )
