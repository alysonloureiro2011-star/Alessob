from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _clean_text(value: Any) -> str | None:
    text = " ".join(str(value or "").strip().split())
    return text or None


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class OperationBridgeResult:
    ok: bool
    bridge_state: str
    recorded_at: str
    operational_state: str
    staging_allowed: bool
    should_retry: bool
    should_store: bool
    next_step: str
    overall_quality_score: float
    case_strength: str | None
    truth_state: str | None
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OperationBridge:
    """
    Ponte entre decisão, memória e operação.

    Função:
    - resumir o estado do ciclo
    - indicar o próximo passo
    - preparar integração futura com staging e learning
    """

    def run(
        self,
        *,
        premium_decision: dict[str, Any] | None = None,
        learning_signal: dict[str, Any] | None = None,
        quality_memory: dict[str, Any] | None = None,
        publish_truth: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        premium_decision = _safe_dict(premium_decision)
        learning_signal = _safe_dict(learning_signal)
        quality_memory = _safe_dict(quality_memory)
        publish_truth = _safe_dict(publish_truth)

        decision_state = _clean_text(premium_decision.get("decision_state")) or "blocked"
        overall_quality_score = _safe_float(premium_decision.get("overall_quality_score"), 0.0)
        case_strength = _clean_text(learning_signal.get("case_strength"))
        truth_state = _clean_text(publish_truth.get("truth_state"))
        should_retry = bool(learning_signal.get("should_retest"))
        should_store = bool(learning_signal.get("should_promote_to_memory") or quality_memory.get("promote_for_reuse"))

        staging_allowed = decision_state in {"editorial_staging_candidate", "brand_live_candidate"}

        if decision_state == "blocked":
            operational_state = "lab"
            next_step = "melhorar_e_testar"
        elif decision_state == "editorial_staging_candidate":
            operational_state = "staging"
            next_step = "subir_para_staging"
        elif decision_state == "brand_live_candidate" and truth_state == "publish_truth_confirmed":
            operational_state = "ready"
            next_step = "repetir_o_que_funcionou"
        else:
            operational_state = "waiting"
            next_step = "coletar_mais_sinal"

        notes = [
            f"decision_state={decision_state}",
            f"operational_state={operational_state}",
            f"next_step={next_step}",
        ]
        if case_strength:
            notes.append(f"case_strength={case_strength}")
        if truth_state:
            notes.append(f"truth_state={truth_state}")

        result = OperationBridgeResult(
            ok=True,
            bridge_state="operation_bridge_ready",
            recorded_at=datetime.now().isoformat(),
            operational_state=operational_state,
            staging_allowed=staging_allowed,
            should_retry=should_retry,
            should_store=should_store,
            next_step=next_step,
            overall_quality_score=overall_quality_score,
            case_strength=case_strength,
            truth_state=truth_state,
            notes=notes,
        )
        return result.to_dict()


def operation_bridge_examples() -> dict[str, Any]:
    bridge = OperationBridge()
    return {
        "blocked_case": bridge.run(
            premium_decision={"decision_state": "blocked", "overall_quality_score": 7.2},
            learning_signal={"case_strength": "weak", "should_retest": True},
            quality_memory={"promote_for_reuse": False},
            publish_truth={"truth_state": "publish_attempt_recorded"},
        ),
        "staging_case": bridge.run(
            premium_decision={"decision_state": "editorial_staging_candidate", "overall_quality_score": 8.4},
            learning_signal={"case_strength": "medium", "should_retest": True},
            quality_memory={"promote_for_reuse": False},
            publish_truth={"truth_state": "publish_attempt_recorded"},
        ),
        "ready_case": bridge.run(
            premium_decision={"decision_state": "brand_live_candidate", "overall_quality_score": 8.9},
            learning_signal={"case_strength": "strong", "should_retest": False, "should_promote_to_memory": True},
            quality_memory={"promote_for_reuse": True},
            publish_truth={"truth_state": "publish_truth_confirmed"},
        ),
    }
