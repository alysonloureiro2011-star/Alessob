from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


@dataclass(frozen=True)
class PostProductionPlan:
    ok: bool
    post_state: str
    cut_strategy: str
    motion_strategy: str
    sound_strategy: str
    subtitle_strategy: str
    final_qc_focus: list[str]
    forbidden_traits: list[str]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PostProductionPipeline:
    """
    Camada soberana de pós-produção.

    Função:
    - consolidar decisões de storyboard, ritmo e legenda
    - orientar corte, motion, som e revisão final
    - preparar o caminho para um pipeline premium real
    """

    def run(
        self,
        *,
        storyboard: dict[str, Any] | None = None,
        rhythm: dict[str, Any] | None = None,
        subtitles: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        storyboard = _safe_dict(storyboard)
        rhythm = _safe_dict(rhythm)
        subtitles = _safe_dict(subtitles)

        scene_count = int(storyboard.get("scene_count") or 0)
        cut_density = str(rhythm.get("target_cut_density") or "medium_controlled").strip()
        subtitle_mode = str(subtitles.get("emphasis_mode") or "balanced_lines").strip()

        if scene_count >= 4 and cut_density == "high_controlled":
            cut_strategy = "cinematic_fast_precision"
        else:
            cut_strategy = "cinematic_balanced_precision"

        if subtitle_mode in {"keyword_punch", "short_emphasis_lines"}:
            motion_strategy = "micro_zoom_plus_clean_reframes"
            sound_strategy = "accent_hits_plus_clean_bed"
        else:
            motion_strategy = "clean_reframes_only"
            sound_strategy = "clean_bed_with_light_accents"

        plan = PostProductionPlan(
            ok=True,
            post_state="post_production_ready",
            cut_strategy=cut_strategy,
            motion_strategy=motion_strategy,
            sound_strategy=sound_strategy,
            subtitle_strategy=subtitle_mode,
            final_qc_focus=[
                "zero_dead_air",
                "hook_strength",
                "subtitle_legibility",
                "sound_clarity",
                "brand_dignity",
            ],
            forbidden_traits=[
                "efeito sem função",
                "poluição visual",
                "corte caótico",
                "som encobrindo a voz",
                "cara de template barato",
            ],
            notes=[
                f"scene_count={scene_count}",
                f"cut_density={cut_density}",
                f"subtitle_mode={subtitle_mode}",
            ],
        )
        return plan.to_dict()


def post_production_examples() -> dict[str, Any]:
    pipeline = PostProductionPipeline()
    return pipeline.run(
        storyboard={"scene_count": 4},
        rhythm={"target_cut_density": "high_controlled"},
        subtitles={"emphasis_mode": "keyword_punch"},
    )
