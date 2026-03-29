from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import re
from typing import Any


_BREAK_CHARS = re.compile(r"[.!?;:\n]+")
_EMPHASIS_WORDS = {
    "agora", "nunca", "segredo", "erro", "verdade", "invisível", "urgente", "atenção",
    "pare", "olha", "muda", "prova", "real", "domina", "perde", "ganha",
}


@dataclass(frozen=True)
class SubtitleCue:
    index: int
    start_ms: int
    end_ms: int
    text: str
    emphasis_words: list[str]
    animation: str
    placement: str
    weight: str
    color_role: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SubtitleIntelligence:
    """Camada aditiva para legendas de reels com tipografia emocional.

    Objetivo: gerar cues legíveis, curtos e com ênfase visual previsível.
    """

    def build(
        self,
        *,
        script_text: str,
        content_type: str = "reel",
        hook_text: str | None = None,
    ) -> dict[str, Any]:
        content_type = str(content_type or "reel").strip().lower() or "reel"
        script_text = str(script_text or "").strip()
        hook_text = str(hook_text or "").strip()
        seed = f"{content_type}|{hook_text}|{script_text}"

        normalized = self._normalize(script_text=script_text, hook_text=hook_text)
        segments = self._segments(normalized)
        cues = self._cues(segments=segments, seed=seed, content_type=content_type)

        return {
            "ok": True,
            "engine": "SubtitleIntelligence",
            "content_type": content_type,
            "seed_key": seed,
            "deterministic": True,
            "subtitle_style": {
                "font_role": "semibold_sans",
                "case_style": "sentence_case",
                "max_lines": 2,
                "safe_zone": "bottom_center_9x16",
                "hook_mode": "first_cue_high_contrast",
            },
            "cues": [cue.to_dict() for cue in cues],
            "hook_overlay": cues[0].to_dict() if cues else None,
        }

    def _normalize(self, *, script_text: str, hook_text: str) -> str:
        base = " ".join(part for part in [hook_text, script_text] if part).strip()
        base = re.sub(r"\s+", " ", base)
        return base

    def _segments(self, text: str) -> list[str]:
        if not text:
            return []
        raw = [chunk.strip() for chunk in _BREAK_CHARS.split(text) if chunk.strip()]
        segments: list[str] = []
        for chunk in raw:
            pieces = self._soft_wrap(chunk)
            for piece in pieces:
                cleaned = piece.strip(" ,-")
                if cleaned:
                    segments.append(cleaned)
        return segments[:12]

    def _soft_wrap(self, text: str) -> list[str]:
        words = text.split()
        if len(words) <= 7:
            return [text]
        wrapped: list[str] = []
        current: list[str] = []
        for word in words:
            current.append(word)
            if len(current) >= 6:
                wrapped.append(" ".join(current))
                current = []
        if current:
            wrapped.append(" ".join(current))
        return wrapped

    def _cues(self, *, segments: list[str], seed: str, content_type: str) -> list[SubtitleCue]:
        cues: list[SubtitleCue] = []
        cursor_ms = 0
        for index, segment in enumerate(segments):
            duration_ms = _duration_for_segment(segment=segment, index=index, content_type=content_type)
            cue_seed = f"{seed}|{index}|{segment.lower()}"
            emphasis_words = _emphasis_words(segment)
            cue = SubtitleCue(
                index=index,
                start_ms=cursor_ms,
                end_ms=cursor_ms + duration_ms,
                text=_display_text(segment),
                emphasis_words=emphasis_words,
                animation=_animation(cue_seed, index=index),
                placement=_placement(index=index),
                weight=_weight(index=index, emphasis_words=emphasis_words),
                color_role=_color_role(index=index, emphasis_words=emphasis_words),
            )
            cues.append(cue)
            cursor_ms += duration_ms
        return cues


def build_subtitle_package(
    *,
    script_text: str,
    content_type: str = "reel",
    hook_text: str | None = None,
) -> dict[str, Any]:
    engine = SubtitleIntelligence()
    return engine.build(script_text=script_text, content_type=content_type, hook_text=hook_text)


def _duration_for_segment(*, segment: str, index: int, content_type: str) -> int:
    words = max(len(segment.split()), 1)
    base = 1050 if content_type == "reel" else 1350
    duration = base + (words * 120)
    if index == 0:
        duration -= 120
    return max(duration, 700)


def _display_text(segment: str) -> str:
    text = re.sub(r"\s+", " ", segment).strip()
    if len(text) > 64:
        text = text[:61].rstrip() + "..."
    return text


def _emphasis_words(segment: str) -> list[str]:
    words = re.findall(r"[a-zà-ÿ0-9_]+", segment.lower())
    selected: list[str] = []
    for word in words:
        if word in _EMPHASIS_WORDS and word not in selected:
            selected.append(word)
    if not selected and words:
        longest = sorted(words, key=lambda item: (-len(item), item))[0]
        selected.append(longest)
    return selected[:2]


def _animation(seed: str, *, index: int) -> str:
    options = ("pop_in", "slide_up", "punch_scale", "cut_in")
    if index == 0:
        return "hook_pop"
    return options[_stable_index(seed=seed, size=len(options))]


def _placement(*, index: int) -> str:
    if index == 0:
        return "center_lower_third"
    return "bottom_center_safe"


def _weight(*, index: int, emphasis_words: list[str]) -> str:
    if index == 0 or emphasis_words:
        return "700"
    return "600"


def _color_role(*, index: int, emphasis_words: list[str]) -> str:
    if index == 0:
        return "high_contrast_primary"
    if emphasis_words:
        return "accent_emphasis"
    return "base_readable"


def _stable_index(*, seed: str, size: int) -> int:
    digest = sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % max(size, 1)
