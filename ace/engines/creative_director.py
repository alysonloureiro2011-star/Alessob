import random
from typing import Dict


VISUAL_MOODS = [
    "cinematic_dark",
    "clean_luxury",
    "warm_human",
    "high_contrast_modern",
    "intimate_closeup"
]

CAMERA_STYLES = [
    "close_face",
    "medium_portrait",
    "slow_push_in",
    "handheld_natural",
    "static_premium"
]

LIGHTING_STYLES = [
    "soft_side_light",
    "golden_hour",
    "studio_clean",
    "dramatic_shadow",
    "natural_window"
]

COLOR_PALETTES = [
    "gold_black",
    "warm_beige_brown",
    "deep_blue_silver",
    "soft_white_skin",
    "earth_luxury"
]

HOOK_OPENINGS = [
    "question_impact",
    "truth_bomb",
    "forbidden_secret",
    "pain_point",
    "unexpected_contrast"
]

RHYTHM_TYPES = [
    "slow_burn",
    "fast_hook",
    "measured_premium",
    "high_tension",
    "emotional_wave"
]


class CreativeDirector:

    def __init__(self):
        self.memory = []

    def choose_visual_mood(self, intensity: str) -> str:
        if intensity == "forte":
            return random.choice([
                "cinematic_dark",
                "high_contrast_modern",
                "intimate_closeup"
            ])
        if intensity == "media":
            return random.choice([
                "clean_luxury",
                "warm_human",
                "high_contrast_modern"
            ])
        return random.choice([
            "warm_human",
            "clean_luxury",
            "soft_white_skin"
        ])

    def choose_camera_style(self, content_type: str) -> str:
        if content_type == "reel":
            return random.choice([
                "close_face",
                "slow_push_in",
                "handheld_natural",
                "medium_portrait"
            ])
        return random.choice([
            "static_premium",
            "medium_portrait",
            "close_face"
        ])

    def choose_lighting(self, mood: str) -> str:
        mapping = {
            "cinematic_dark": "dramatic_shadow",
            "clean_luxury": "studio_clean",
            "warm_human": "natural_window",
            "high_contrast_modern": "soft_side_light",
            "intimate_closeup": "golden_hour",
        }
        return mapping.get(mood, "studio_clean")

    def choose_palette(self, mood: str) -> str:
        mapping = {
            "cinematic_dark": "gold_black",
            "clean_luxury": "soft_white_skin",
            "warm_human": "warm_beige_brown",
            "high_contrast_modern": "deep_blue_silver",
            "intimate_closeup": "earth_luxury",
        }
        return mapping.get(mood, "soft_white_skin")

    def choose_hook_opening(self, style: str) -> str:
        mapping = {
            "choque": "truth_bomb",
            "curiosidade": "question_impact",
            "segredo": "forbidden_secret",
            "historia": "pain_point",
            "autoridade": "unexpected_contrast",
        }
        return mapping.get(style, random.choice(HOOK_OPENINGS))

    def choose_rhythm(self, content_type: str, intensity: str) -> str:
        if content_type == "reel" and intensity == "forte":
            return "fast_hook"
        if content_type == "reel":
            return random.choice(["measured_premium", "emotional_wave", "fast_hook"])
        return random.choice(["slow_burn", "measured_premium", "high_tension"])

    def build_direction(self, decision: Dict) -> Dict:
        content_type = decision.get("content_type", "reel")
        style = decision.get("style", "autoridade")
        intensity = decision.get("intensity", "media")
        trend = decision.get("trend", "")

        mood = self.choose_visual_mood(intensity)
        camera = self.choose_camera_style(content_type)
        lighting = self.choose_lighting(mood)
        palette = self.choose_palette(mood)
        hook_opening = self.choose_hook_opening(style)
        rhythm = self.choose_rhythm(content_type, intensity)

        direction = {
            "trend": trend,
            "content_type": content_type,
            "style": style,
            "intensity": intensity,
            "visual_mood": mood,
            "camera_style": camera,
            "lighting": lighting,
            "palette": palette,
            "hook_opening": hook_opening,
            "rhythm": rhythm,
            "quality_target": "premium_natural",
            "humanization": "high",
            "dopamine_target": "controlled_high_retention"
        }

        self.memory.append(direction)
        if len(self.memory) > 100:
            self.memory.pop(0)

        return direction


creative_director = CreativeDirector()
