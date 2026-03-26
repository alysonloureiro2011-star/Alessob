from dataclasses import dataclass, asdict
from typing import Any, Dict


def _safe_dict(value: Any) -> Dict:
    return dict(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


@dataclass
class ReelDirectorResult:
    ok: bool
    state: str
    visual_mode: str
    cut_mode: str
    audio_mode: str
    subtitle_mode: str
    notes: list

    def to_dict(self):
        return asdict(self)


class ReelDirector:

    def run(
        self,
        *,
        hook_opening: Dict | None = None,
        storyboard: Dict | None = None,
        rhythm: Dict | None = None,
        subtitles: Dict | None = None,
    ) -> Dict:
        hook_opening = _safe_dict(hook_opening)
        storyboard = _safe_dict(storyboard)
        rhythm = _safe_dict(rhythm)
        subtitles = _safe_dict(subtitles)

        opening = _clean_text(hook_opening.get("opening_pattern") or "curiosity_gap")
        scenes = int(storyboard.get("scene_count") or 0)
        density = _clean_text(rhythm.get("target_cut_density") or "medium_controlled")
        subtitle_mode = _clean_text(subtitles.get("emphasis_mode") or "balanced_lines")

        if opening in {"authority_shock", "curiosity_gap"} and scenes >= 4:
            visual_mode = "cinematic_retention"
        else:
            visual_mode = "cinematic_clean"

        if density == "high_controlled":
            cut_mode = "precision_fast"
            audio_mode = "accented"
        else:
            cut_mode = "precision_balanced"
            audio_mode = "clean"

        return ReelDirectorResult(
            ok=True,
            state="reel_director_ready",
            visual_mode=visual_mode,
            cut_mode=cut_mode,
            audio_mode=audio_mode,
            subtitle_mode=subtitle_mode,
            notes=[f"opening={opening}", f"scenes={scenes}", f"density={density}"],
        ).to_dict()
