from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class DistributionDecision:
    ok: bool
    distribution_state: str
    distribution_track: str
    repeat_winner: bool
    serial_candidate: bool
    first_comment_enabled: bool
    notes: list[str]
    guardrails: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DistributionHeuristics:
    """
    Camada soberana de distribuição.

    Função:
    - decidir trilha de distribuição com base em qualidade e evidência
    - indicar se o caso pede repetição de vencedor ou continuidade serial
    - preparar a lógica de primeiro comentário e reforço de distribuição
    """

    def run(
        self,
        *,
        premium_decision: dict[str, Any] | None = None,
        learning_signal: dict[str, Any] | None = None,
        operation_bridge: dict[str, Any] | None = None,
        platform_contract: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        premium_decision = _safe_dict(premium_decision)
        learning_signal = _safe_dict(learning_signal)
        operation_bridge = _safe_dict(operation_bridge)
        platform_contract = _safe_dict(platform_contract)

        quality = _safe_float(premium_decision.get("overall_quality_score"), 0.0)
        decision_state = _clean_text(premium_decision.get("decision_state")) or "blocked"
        case_strength = _clean_text(learning_signal.get("case_strength")) or "weak"
        operational_state = _clean_text(operation_bridge.get("operational_state")) or "lab"
        allows_first_comment = bool(platform_contract.get("allows_first_comment"))

        repeat_winner = quality >= 8.8 and case_strength == "strong"
        serial_candidate = quality >= 8.0 and decision_state != "blocked"
        first_comment_enabled = allows_first_comment and decision_state != "blocked"

        if repeat_winner and operational_state in {"ready", "staging"}:
            distribution_track = "winner_expansion"
        elif serial_candidate:
            distribution_track = "serial_growth"
        elif decision_state == "blocked":
            distribution_track = "lab_retry"
        else:
            distribution_track = "signal_collection"

        decision = DistributionDecision(
            ok=True,
            distribution_state="distribution_heuristics_ready",
            distribution_track=distribution_track,
            repeat_winner=repeat_winner,
            serial_candidate=serial_candidate,
            first_comment_enabled=first_comment_enabled,
            notes=[
                f"decision_state={decision_state}",
                f"case_strength={case_strength}",
                f"operational_state={operational_state}",
            ],
            guardrails=[
                "distribuicao_nao_salva_peca_fraca",
                "repetir_vencedor_sem_spam",
                "serialidade_com_coerencia",
            ],
        )
        return decision.to_dict()


def distribution_heuristics_examples() -> dict[str, Any]:
    engine = DistributionHeuristics()
    return {
        "winner_case": engine.run(
            premium_decision={"overall_quality_score": 8.9, "decision_state": "brand_live_candidate"},
            learning_signal={"case_strength": "strong"},
            operation_bridge={"operational_state": "ready"},
            platform_contract={"allows_first_comment": True},
        ),
        "serial_case": engine.run(
            premium_decision={"overall_quality_score": 8.2, "decision_state": "editorial_staging_candidate"},
            learning_signal={"case_strength": "medium"},
            operation_bridge={"operational_state": "staging"},
            platform_contract={"allows_first_comment": True},
        ),
    }
