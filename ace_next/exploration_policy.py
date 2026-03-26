from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


SAFE_EXPLORE_ACTIONS = {
    "test_new_hook",
    "test_new_opening",
    "test_new_template",
    "test_new_timing",
}

SAFE_EXPLOIT_ACTIONS = {
    "repeat_winner",
    "double_down_format",
    "promote_series_candidate",
}


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _clean_text(value: Any) -> str | None:
    text = " ".join(str(value or "").strip().split())
    return text or None


@dataclass(frozen=True)
class ExplorationPolicyDecision:
    ok: bool
    policy_state: str
    policy_mode: str
    recommended_track: str
    recommended_action: str | None
    can_explore: bool
    can_exploit: bool
    notes: list[str]
    guardrails: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ExplorationPolicy:
    """
    Politica conservadora para exploracao vs aproveitamento.

    Funcao:
    - impedir improviso burro
    - dizer quando explorar com seguranca
    - dizer quando aproveitar vencedor sem virar spam
    """

    def run(
        self,
        *,
        recommendation_engine: dict[str, Any] | None = None,
        experiment_resolution: dict[str, Any] | None = None,
        evidence_interpreter: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        recommendation_engine = _safe_dict(recommendation_engine)
        experiment_resolution = _safe_dict(experiment_resolution)
        evidence_interpreter = _safe_dict(evidence_interpreter)

        recommended_action = _clean_text(recommendation_engine.get("recommended_action"))
        resolution_state = _clean_text(experiment_resolution.get("resolution_state")) or "collecting"
        evidence_state = _clean_text(evidence_interpreter.get("evidence_state")) or "unknown"

        if recommended_action in SAFE_EXPLORE_ACTIONS:
            policy_mode = "explore"
            recommended_track = "controlled_exploration"
            can_explore = True
            can_exploit = False
        elif recommended_action in SAFE_EXPLOIT_ACTIONS:
            policy_mode = "exploit"
            recommended_track = "controlled_exploitation"
            can_explore = False
            can_exploit = True
        elif resolution_state == "resolved_winner":
            policy_mode = "exploit"
            recommended_track = "winner_expansion"
            can_explore = False
            can_exploit = True
        else:
            policy_mode = "observe"
            recommended_track = "collect_more_signal"
            can_explore = False
            can_exploit = False

        notes = [
            f"resolution_state={resolution_state}",
            f"evidence_state={evidence_state}",
            f"recommended_action={recommended_action or 'none'}",
        ]

        decision = ExplorationPolicyDecision(
            ok=True,
            policy_state="exploration_policy_ready",
            policy_mode=policy_mode,
            recommended_track=recommended_track,
            recommended_action=recommended_action,
            can_explore=can_explore,
            can_exploit=can_exploit,
            notes=notes,
            guardrails=[
                "nao justificar spam",
                "nao abrir exploracao sem hipotese",
                "nao repetir vencedor sem quality gate",
                "preservar marca acima de volume",
            ],
        )
        return decision.to_dict()


def exploration_policy_examples() -> dict[str, Any]:
    policy = ExplorationPolicy()
    return {
        "explore_case": policy.run(
            recommendation_engine={"recommended_action": "test_new_hook"},
            experiment_resolution={"resolution_state": "collecting"},
            evidence_interpreter={"evidence_state": "weak_signal"},
        ),
        "exploit_case": policy.run(
            recommendation_engine={"recommended_action": "repeat_winner"},
            experiment_resolution={"resolution_state": "resolved_winner"},
            evidence_interpreter={"evidence_state": "strong_evidence"},
        ),
    }
