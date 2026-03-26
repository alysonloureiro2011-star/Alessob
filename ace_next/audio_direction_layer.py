from dataclasses import dataclass, asdict
from typing import Any, Dict


def _safe_dict(value: Any) -> Dict:
    return dict(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


@dataclass
class AudioDirectionResult:
    ok: bool
    state: str
    voice_mode: str
    music_mode: str
    foley_mode: str
    mix_mode: str
    notes: list

    def to_dict(self):
        return asdict(self)


class AudioDirectionLayer:

    def run(
        self,
        *,
        hook_opening: Dict | None = None,
        rhythm: Dict | None = None,
        post_production: Dict | None = None,
    ) -> Dict:
        hook_opening = _safe_dict(hook_opening)
        rhythm = _safe_dict(rhythm)
        post_production = _safe_dict(post_production)

        opening = _clean_text(hook_opening.get("opening_pattern") or "curiosity_gap")
        density = _clean_text(rhythm.get("target_cut_density") or "medium_controlled")
        sound_strategy = _clean_text(post_production.get("sound_strategy") or "clean_bed_with_light_accents")

        if opening in {"authority_shock", "curiosity_gap"}:
            voice_mode = "assertive_clear"
        else:
            voice_mode = "balanced_clear"

        if density == "high_controlled":
            music_mode = "accented_bed"
            foley_mode = "micro_hits"
        else:
            music_mode = "clean_bed"
            foley_mode = "light_texture"

        if "accent" in sound_strategy:
            mix_mode = "dynamic_mix"
        else:
            mix_mode = "clean_mix"

        return AudioDirectionResult(
            ok=True,
            state="audio_direction_layer_ready",
            voice_mode=voice_mode,
            music_mode=music_mode,
            foley_mode=foley_mode,
            mix_mode=mix_mode,
            notes=[f"opening={opening}", f"density={density}", f"sound={sound_strategy}"],
        ).to_dict()
