from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import re
from typing import Any


_STOPWORDS = {
    "a", "as", "o", "os", "e", "de", "da", "do", "das", "dos", "para", "por", "com",
    "sem", "em", "no", "na", "nos", "nas", "um", "uma", "uns", "umas", "que", "se",
    "como", "mais", "menos", "muito", "muita", "sobre", "isso", "essa", "esse", "esta",
    "este", "sua", "seu", "suas", "seus", "você", "vocês", "ele", "ela", "eles", "elas",
}


_FORMAT_HOUR_MATRIX: dict[str, dict[str, tuple[str, ...]]] = {
    "reel": {
        "weekday": ("11:40", "18:50", "21:10"),
        "weekend": ("10:30", "17:40", "20:40"),
    },
    "carousel": {
        "weekday": ("07:20", "12:20", "20:20"),
        "weekend": ("09:10", "18:10", "20:50"),
    },
    "story": {
        "weekday": ("08:00", "13:10", "19:15"),
        "weekend": ("09:30", "14:20", "19:40"),
    },
    "image": {
        "weekday": ("11:20", "18:20", "20:40"),
        "weekend": ("10:40", "17:20", "20:20"),
    },
}


@dataclass(frozen=True)
class TimingRecommendation:
    format: str
    day_profile: str
    primary_window: str
    secondary_windows: list[str]
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SerialityRecommendation:
    series_key: str
    episode_label: str
    sequel_hook: str
    continuity_anchor: str
    rationale: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SeoSocialEngine:
    """Camada aditiva para timing, serialidade e SEO social.

    Não toca no runtime soberano. Apenas prepara um pacote determinístico que pode ser
    conectado depois ao fluxo oficial.
    """

    def __init__(self, platform: str = "instagram", locale: str = "pt_BR") -> None:
        self.platform = str(platform or "instagram").strip().lower()
        self.locale = str(locale or "pt_BR").strip() or "pt_BR"

    def recommend(
        self,
        *,
        creative_plan: dict[str, Any] | None,
        recent_records: list[dict[str, Any]] | None = None,
        performance_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        creative_plan = dict(creative_plan or {})
        recent_records = list(recent_records or [])
        performance_context = dict(performance_context or {})

        content_format = _normalize_format(
            creative_plan.get("publish_format_now")
            or creative_plan.get("strategic_target_format")
            or creative_plan.get("format_recommendation")
            or "reel"
        )
        day_profile = _resolve_day_profile(creative_plan)
        seed = _seed_key(creative_plan=creative_plan, content_format=content_format)
        tokens = _extract_tokens(creative_plan)
        primary_keywords = _top_keywords(tokens, limit=5)
        hashtags = _hashtags_from_keywords(primary_keywords)
        on_screen_keywords = primary_keywords[:3]
        timing = self._timing_recommendation(content_format=content_format, day_profile=day_profile, seed=seed)
        seriality = self._seriality_recommendation(
            creative_plan=creative_plan,
            recent_records=recent_records,
            keywords=primary_keywords,
            content_format=content_format,
        )
        distribution_focus = _distribution_focus(content_format)
        ranking_targets = _ranking_targets(content_format)
        caption_angle = _caption_angle(creative_plan=creative_plan, keywords=primary_keywords)
        recommendation_reason = _recommendation_reason(
            performance_context=performance_context,
            content_format=content_format,
            ranking_targets=ranking_targets,
        )

        return {
            "ok": True,
            "engine": "SeoSocialEngine",
            "platform": self.platform,
            "locale": self.locale,
            "content_format": content_format,
            "primary_keywords": primary_keywords,
            "on_screen_keywords": on_screen_keywords,
            "hashtags": hashtags,
            "caption_angle": caption_angle,
            "timing_recommendation": timing.to_dict(),
            "format_hour_matrix": _matrix_snapshot(content_format),
            "seriality_recommendation": seriality.to_dict(),
            "distribution_focus": distribution_focus,
            "ranking_targets": ranking_targets,
            "recommendation_reason": recommendation_reason,
            "deterministic": True,
            "seed_key": seed,
        }

    def _timing_recommendation(self, *, content_format: str, day_profile: str, seed: str) -> TimingRecommendation:
        matrix = _FORMAT_HOUR_MATRIX.get(content_format, _FORMAT_HOUR_MATRIX["image"])
        windows = list(matrix.get(day_profile, matrix["weekday"]))
        primary_index = _stable_index(seed=f"{seed}|{day_profile}|timing", size=len(windows))
        primary_window = windows[primary_index]
        secondary_windows = [window for idx, window in enumerate(windows) if idx != primary_index]
        rationale = (
            f"prioriza {content_format} em janela de {day_profile} com equilíbrio entre descoberta, "
            "retenção inicial e reentrada noturna"
        )
        return TimingRecommendation(
            format=content_format,
            day_profile=day_profile,
            primary_window=primary_window,
            secondary_windows=secondary_windows,
            rationale=rationale,
        )

    def _seriality_recommendation(
        self,
        *,
        creative_plan: dict[str, Any],
        recent_records: list[dict[str, Any]],
        keywords: list[str],
        content_format: str,
    ) -> SerialityRecommendation:
        root = "-".join(keywords[:3]) or content_format
        series_key = f"{content_format}:{root}"
        episode_number = _episode_number(series_key=series_key, recent_records=recent_records)
        headline = str(creative_plan.get("headline") or creative_plan.get("hook") or "").strip()
        theme = keywords[0] if keywords else content_format
        sequel_hook = (
            f"episódio seguinte: a consequência invisível de {theme}"
            if episode_number == 1
            else f"continuação: o detalhe que faltou sobre {theme}"
        )
        continuity_anchor = headline or f"série sobre {theme}"
        rationale = "serialidade curta para aumentar retorno, saves e consumo encadeado"
        return SerialityRecommendation(
            series_key=series_key,
            episode_label=f"EP{episode_number:02d}",
            sequel_hook=sequel_hook,
            continuity_anchor=continuity_anchor,
            rationale=rationale,
        )


def build_seo_social_package(
    *,
    creative_plan: dict[str, Any] | None,
    recent_records: list[dict[str, Any]] | None = None,
    performance_context: dict[str, Any] | None = None,
    platform: str = "instagram",
    locale: str = "pt_BR",
) -> dict[str, Any]:
    engine = SeoSocialEngine(platform=platform, locale=locale)
    return engine.recommend(
        creative_plan=creative_plan,
        recent_records=recent_records,
        performance_context=performance_context,
    )


def _seed_key(*, creative_plan: dict[str, Any], content_format: str) -> str:
    basis = "|".join(
        [
            str(creative_plan.get("trend") or "").strip(),
            str(creative_plan.get("headline") or "").strip(),
            str(creative_plan.get("hook") or "").strip(),
            content_format,
        ]
    )
    return basis or content_format


def _normalize_format(value: Any) -> str:
    text = str(value or "image").strip().lower()
    aliases = {
        "reels": "reel",
        "stories": "story",
        "carrossel": "carousel",
        "carrousel": "carousel",
        "post": "image",
        "feed": "image",
    }
    return aliases.get(text, text or "image")


def _resolve_day_profile(creative_plan: dict[str, Any]) -> str:
    timing = str(creative_plan.get("timing_hypothesis") or "").lower()
    if any(token in timing for token in ("weekend", "sábado", "domingo", "fim de semana")):
        return "weekend"
    return "weekday"


def _extract_tokens(creative_plan: dict[str, Any]) -> list[str]:
    pool = " ".join(
        [
            str(creative_plan.get("trend") or ""),
            str(creative_plan.get("headline") or ""),
            str(creative_plan.get("hook") or ""),
            str(creative_plan.get("caption_core") or ""),
            str(creative_plan.get("goal") or ""),
        ]
    ).lower()
    raw_tokens = re.findall(r"[a-zà-ÿ0-9_]{3,}", pool)
    return [token for token in raw_tokens if token not in _STOPWORDS]


def _top_keywords(tokens: list[str], limit: int) -> list[str]:
    scores: dict[str, int] = {}
    for token in tokens:
        scores[token] = scores.get(token, 0) + 1
    ranked = sorted(scores.items(), key=lambda item: (-item[1], -len(item[0]), item[0]))
    return [token for token, _ in ranked[:limit]]


def _hashtags_from_keywords(keywords: list[str]) -> list[str]:
    hashtags: list[str] = []
    for keyword in keywords:
        normalized = re.sub(r"[^a-zà-ÿ0-9]", "", keyword.lower())
        if not normalized:
            continue
        tag = f"#{normalized}"
        if tag not in hashtags:
            hashtags.append(tag)
    if "#reels" not in hashtags:
        hashtags.append("#reels")
    return hashtags[:8]


def _caption_angle(*, creative_plan: dict[str, Any], keywords: list[str]) -> str:
    goal = str(creative_plan.get("goal") or "atenção profunda").strip().lower()
    theme = keywords[0] if keywords else "tema"
    return f"abrir com tensão clara, entregar valor prático sobre {theme} e fechar com CTA de save/share alinhado a {goal}"


def _matrix_snapshot(content_format: str) -> dict[str, Any]:
    matrix = _FORMAT_HOUR_MATRIX.get(content_format, _FORMAT_HOUR_MATRIX["image"])
    return {
        "weekday": list(matrix["weekday"]),
        "weekend": list(matrix["weekend"]),
    }


def _distribution_focus(content_format: str) -> list[str]:
    if content_format == "reel":
        return ["non_follower_discovery", "watch_time", "completion"]
    if content_format == "carousel":
        return ["saves", "swipe_depth", "shares_dm"]
    if content_format == "story":
        return ["relationship_graph", "reply_rate", "tap_forward_control"]
    return ["reach", "saves", "shares_dm"]


def _ranking_targets(content_format: str) -> list[str]:
    base = ["shares_dm", "save_rate", "completion_rate"]
    if content_format == "reel":
        return base + ["watch_time_ms", "replay_rate"]
    if content_format == "carousel":
        return base + ["swipe_depth", "hold_rate"]
    return base + ["ctr_profile", "comment_quality"]


def _recommendation_reason(*, performance_context: dict[str, Any], content_format: str, ranking_targets: list[str]) -> str:
    learning_state = str(performance_context.get("learning_state") or "cold_start")
    return (
        f"{content_format} orientado por {learning_state}, priorizando {ranking_targets[0]} e {ranking_targets[1]} "
        "como sinais profundos de distribuição"
    )


def _episode_number(*, series_key: str, recent_records: list[dict[str, Any]]) -> int:
    hits = 0
    for record in recent_records:
        record_series = str(record.get("series_key") or record.get("series_name") or "").strip().lower()
        if record_series == series_key.lower():
            hits += 1
            continue
        creative_plan = record.get("creative_plan") if isinstance(record.get("creative_plan"), dict) else {}
        record_headline = str(creative_plan.get("headline") or record.get("headline") or "").lower()
        if series_key.split(":", 1)[-1].split("-")[0] and series_key.split(":", 1)[-1].split("-")[0] in record_headline:
            hits += 1
    return hits + 1


def _stable_index(*, seed: str, size: int) -> int:
    digest = sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % max(size, 1)
