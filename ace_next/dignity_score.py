from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DignityBreakdown:
    clarity_score: float
    coherence_score: float
    restraint_score: float
    readability_score: float
    quality_score: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DignityScore:
    def evaluate(
        self,
        *,
        creative_plan: dict[str, Any] | None,
        subtitle_package: dict[str, Any] | None = None,
        visual_qa: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        creative_plan = dict(creative_plan or {})
        subtitle_package = dict(subtitle_package or {})
        visual_qa = dict(visual_qa or {})

        headline = str(creative_plan.get("headline") or "").strip()
        hook = str(creative_plan.get("hook") or "").strip()
        body = str(creative_plan.get("body") or "").strip()
        cta = str(creative_plan.get("cta") or "").strip()
        cues = list(subtitle_package.get("cues") or [])

        headline_len = len(headline)
        hook_len = len(hook)
        cue_count = len(cues)
        punctuation_density = _punctuation_density(" ".join([headline, hook, body, cta]))
        all_caps_ratio = _all_caps_ratio(" ".join([headline, hook, cta]))
        final_score = _to_float(visual_qa.get("final_score"), default=80.0)

        clarity_score = _bounded(10.0 - max(0, headline_len - 72) * 0.06 - punctuation_density * 8.0)
        coherence_score = _bounded(8.0 + min(cue_count, 6) * 0.18 - abs(headline_len - hook_len) * 0.01)
        restraint_score = _bounded(10.0 - all_caps_ratio * 12.0 - punctuation_density * 6.0)
        readability_score = _bounded(9.5 - max(0, cue_count - 10) * 0.30)
        quality_score = _bounded(final_score / 10.0)

        total = round(
            clarity_score * 0.24
            + coherence_score * 0.20
            + restraint_score * 0.18
            + readability_score * 0.18
            + quality_score * 0.20,
            2,
        )

        reasons: list[str] = []
        recommendations: list[str] = []

        if clarity_score >= 8.0:
            reasons.append("mensagem central clara")
        else:
            recommendations.append("encurtar headline e reduzir excesso de pontuacao")

        if restraint_score >= 8.0:
            reasons.append("tom contido e limpo")
        else:
            recommendations.append("reduzir caixa alta e sensacionalismo visual")

        if readability_score < 7.5:
            recommendations.append("reduzir densidade de cues e preservar leitura")

        approved = total >= 7.6
        return {
            "ok": True,
            "engine": "DignityScore",
            "approved": approved,
            "score": total,
            "breakdown": DignityBreakdown(
                clarity_score=clarity_score,
                coherence_score=coherence_score,
                restraint_score=restraint_score,
                readability_score=readability_score,
                quality_score=quality_score,
            ).to_dict(),
            "reasons": reasons,
            "recommendations": _dedupe(recommendations),
        }


def evaluate_dignity(
    *,
    creative_plan: dict[str, Any] | None,
    subtitle_package: dict[str, Any] | None = None,
    visual_qa: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return DignityScore().evaluate(
        creative_plan=creative_plan,
        subtitle_package=subtitle_package,
        visual_qa=visual_qa,
    )


def _bounded(value: float) -> float:
    return round(max(0.0, min(value, 10.0)), 2)


def _to_float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _punctuation_density(text: str) -> float:
    text = str(text or "")
    if not text:
        return 0.0
    punct = sum(1 for ch in text if ch in "!?.,:;-")
    return punct / max(len(text), 1)


def _all_caps_ratio(text: str) -> float:
    words = [word for word in str(text or "").split() if word.isalpha()]
    if not words:
        return 0.0
    caps = sum(1 for word in words if word.isupper() and len(word) > 2)
    return caps / len(words)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered
