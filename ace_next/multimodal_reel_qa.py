from dataclasses import dataclass, asdict
from typing import Any, Dict


def _safe_dict(value: Any) -> Dict:
    return dict(value) if isinstance(value, dict) else {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


@dataclass
class MultimodalQAResult:
    ok: bool
    state: str
    visual_score: float
    audio_score: float
    rhythm_score: float
    natural_score: float
    global_score: float
    approved: bool
    notes: list

    def to_dict(self):
        return asdict(self)


class MultimodalReelQA:

    def run(
        self,
        *,
        visual_gate: Dict | None = None,
        audio_gate: Dict | None = None,
        reel_gate: Dict | None = None,
        naturalism: Dict | None = None,
    ) -> Dict:

        visual_gate = _safe_dict(visual_gate)
        audio_gate = _safe_dict(audio_gate)
        reel_gate = _safe_dict(reel_gate)
        naturalism = _safe_dict(naturalism)

        visual_score = _safe_float(visual_gate.get("global_visual_score"), 0.0)
        audio_score = _safe_float(audio_gate.get("global_audio_score"), 0.0)
        rhythm_score = _safe_float(reel_gate.get("global_score"), 0.0)

        natural_score = 8.2 if naturalism.get("naturalism_state") == "naturalism_engine_ready" else 6.0

        global_score = round(
            (visual_score * 0.3) +
            (audio_score * 0.2) +
            (rhythm_score * 0.3) +
            (natural_score * 0.2),
            2
        )

        approved = global_score >= 8.4

        return MultimodalQAResult(
            ok=True,
            state="multimodal_reel_qa_ready",
            visual_score=visual_score,
            audio_score=audio_score,
            rhythm_score=rhythm_score,
            natural_score=natural_score,
            global_score=global_score,
            approved=approved,
            notes=[
                f"global_score={global_score}",
                f"approved={str(approved).lower()}"
            ]
        ).to_dict()
