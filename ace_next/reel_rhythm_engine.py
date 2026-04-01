from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


@dataclass(frozen=True)
class ReelRhythmResult:
    ok: bool
    rhythm_state: str
    cadence_ms: dict[str, int]
    structure: list[str]
    loop_required: bool
    loop_type: str
    duration_target_sec: int
    subtitle_pacing_hint: str
    retention_mode: str
    micro_payoff_density: str
    notes: dict[str, str]
    study_alignment: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ReelRhythmEngine:
    """
    Engine soberano de ritmo para Reels.

    Compatibilidade exigida pelo runtime:
    - precisa expor .run(...)
    - mantém também .build_rhythm(...) para compatibilidade antiga
    """

    def __init__(self) -> None:
        self.pattern = {
            "0_3s": 450,
            "3_15s": 1200,
            "15_45s": 850,
            "45_55s": 1500,
            "55_60s": 300,
        }
        self.structure = ["hook", "build", "tension", "payoff", "loop"]

    def _result(self, plan: dict[str, Any] | None = None) -> dict[str, Any]:
        plan = _safe_dict(plan)

        subtitle_pacing_hint = "short_emphasis_lines"
        if str(plan.get("publish_format_now") or "").strip().lower() in {"carousel", "image"}:
            subtitle_pacing_hint = "balanced_lines"

        result = ReelRhythmResult(
            ok=True,
            rhythm_state="reel_rhythm_ready",
            cadence_ms=self.pattern,
            structure=self.structure,
            loop_required=True,
            loop_type="invisible",
            duration_target_sec=60,
            subtitle_pacing_hint=subtitle_pacing_hint,
            retention_mode="progressive_micro_payoff",
            micro_payoff_density="high_controlled",
            notes={
                "hook": "primeiros 0-3s obrigatórios",
                "retention": "progressiva com micro payoffs",
                "loop": "fechamento conecta com início",
            },
            study_alignment={
                "hook_attention": True,
                "cadence_control": True,
                "micro_payoff": True,
                "retention_engineering": True,
            },
        )
        return result.to_dict()

    def build_rhythm(self, plan: dict[str, Any]) -> dict[str, Any]:
        return self._result(plan)

    def run(
        self,
        *,
        storyboard: dict[str, Any] | None = None,
        hook_opening: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        storyboard = _safe_dict(storyboard)
        hook_opening = _safe_dict(hook_opening)

        merged_context = {
            **storyboard,
            "hook_opening": hook_opening,
        }
        return self._result(merged_context)


reel_rhythm_engine = ReelRhythmEngine()
