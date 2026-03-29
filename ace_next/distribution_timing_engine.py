from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .seo_social_engine import build_seo_social_package


@dataclass(frozen=True)
class WindowPerformance:
    window: str
    score: float
    sample_size: int
    confidence: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DistributionTimingDecision:
    recommended_window: str
    backup_windows: list[str]
    recommended_format: str
    confidence: str
    rationale: str
    observed_signal: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class DistributionTimingEngine:
    """
    Camada aditiva de timing/distribuição.

    Regras:
    - não toca no runtime soberano
    - não duplica matriz base do seo_social_engine
    - usa seo_social_engine como fundação e só adiciona leitura de sinal recente
    """

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

        seo_package = build_seo_social_package(
            creative_plan=creative_plan,
            recent_records=recent_records,
            performance_context=performance_context,
        )

        timing = dict(seo_package.get("timing_recommendation") or {})
        format_hour_matrix = dict(seo_package.get("format_hour_matrix") or {})
        recommended_format = str(seo_package.get("content_format") or "image")
        primary_window = str(timing.get("primary_window") or "20:20")
        backup_windows = list(timing.get("secondary_windows") or [])

        weekday_windows = list(format_hour_matrix.get("weekday") or [])
        weekend_windows = list(format_hour_matrix.get("weekend") or [])
        candidate_windows = _dedupe([primary_window, *backup_windows, *weekday_windows, *weekend_windows])
        observed_signal = self._observe_window_signal(
            recent_records=recent_records,
            candidate_windows=candidate_windows,
            recommended_format=recommended_format,
        )

        observed_best = str(observed_signal.get("best_window") or "").strip()
        if observed_best:
            recommended_window = observed_best
            remaining = [window for window in candidate_windows if window != recommended_window]
        else:
            recommended_window = primary_window
            remaining = [window for window in candidate_windows if window != recommended_window]

        confidence = _resolve_confidence(
            observed_count=int(observed_signal.get("observed_count") or 0),
            performance_context=performance_context,
        )
        rationale = _build_rationale(
            recommended_format=recommended_format,
            recommended_window=recommended_window,
            observed_signal=observed_signal,
            seo_package=seo_package,
        )

        decision = DistributionTimingDecision(
            recommended_window=recommended_window,
            backup_windows=remaining[:3],
            recommended_format=recommended_format,
            confidence=confidence,
            rationale=rationale,
            observed_signal=observed_signal,
        )

        return {
            "ok": True,
            "engine": "DistributionTimingEngine",
            "seo_social_package": seo_package,
            "decision": decision.to_dict(),
            "deterministic": True,
        }

    def _observe_window_signal(
        self,
        *,
        recent_records: list[dict[str, Any]],
        candidate_windows: list[str],
        recommended_format: str,
    ) -> dict[str, Any]:
        bucket_scores: dict[str, list[float]] = {window: [] for window in candidate_windows}

        for record in recent_records:
            record_format = _normalize_format(
                record.get("content_format")
                or record.get("format")
                or (record.get("creative_plan") or {}).get("publish_format_now")
            )
            if record_format and record_format != recommended_format:
                continue

            published_at = str(record.get("published_at") or record.get("published_time") or "").strip()
            window = _extract_hhmm(published_at)
            if not window or window not in bucket_scores:
                continue

            score = _record_attention_score(record)
            bucket_scores[window].append(score)

        ranking: list[WindowPerformance] = []
        for window, scores in bucket_scores.items():
            if not scores:
                continue
            mean_score = round(sum(scores) / len(scores), 4)
            ranking.append(
                WindowPerformance(
                    window=window,
                    score=mean_score,
                    sample_size=len(scores),
                    confidence=_sample_confidence(len(scores)),
                )
            )

        ranking.sort(key=lambda item: (-item.score, -item.sample_size, item.window))
        best_window = ranking[0].window if ranking else None
        return {
            "observed_count": sum(item.sample_size for item in ranking),
            "best_window": best_window,
            "window_ranking": [item.to_dict() for item in ranking],
        }


def build_distribution_timing_package(
    *,
    creative_plan: dict[str, Any] | None,
    recent_records: list[dict[str, Any]] | None = None,
    performance_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return DistributionTimingEngine().recommend(
        creative_plan=creative_plan,
        recent_records=recent_records,
        performance_context=performance_context,
    )


def _record_attention_score(record: dict[str, Any]) -> float:
    metrics = dict(record.get("real_metrics") or record.get("metrics") or {})
    saved = _safe_float(metrics.get("saved") or metrics.get("saves"))
    shares = _safe_float(metrics.get("shares") or metrics.get("shared"))
    completion = _safe_float(metrics.get("completion_rate") or metrics.get("watch_completion_rate"))
    watch_time = _safe_float(metrics.get("watch_time") or metrics.get("watch_time_ms"))

    score = 0.0
    if saved is not None:
        score += min(saved, 100.0) * 0.25
    if shares is not None:
        score += min(shares, 100.0) * 0.30
    if completion is not None:
        score += min(completion, 100.0) * 0.35
    if watch_time is not None:
        score += min(watch_time / 1000.0, 100.0) * 0.10
    return round(score, 4)


def _build_rationale(
    *,
    recommended_format: str,
    recommended_window: str,
    observed_signal: dict[str, Any],
    seo_package: dict[str, Any],
) -> str:
    observed_count = int(observed_signal.get("observed_count") or 0)
    base_reason = str(seo_package.get("recommendation_reason") or "").strip()
    if observed_count > 0:
        return (
            f"{recommended_format} priorizado em {recommended_window} usando matriz base do SEO social "
            f"e {observed_count} sinais reais recentes. {base_reason}"
        )
    return (
        f"{recommended_format} priorizado em {recommended_window} usando matriz base do SEO social "
        f"sem duplicar regra. {base_reason}"
    )


def _resolve_confidence(*, observed_count: int, performance_context: dict[str, Any]) -> str:
    learning_state = str(performance_context.get("learning_state") or "").strip().lower()
    if observed_count >= 6:
        return "high"
    if observed_count >= 2:
        return "medium"
    if learning_state in {"warming", "stable"}:
        return "medium"
    return "low"


def _sample_confidence(sample_size: int) -> str:
    if sample_size >= 4:
        return "high"
    if sample_size >= 2:
        return "medium"
    return "low"


def _extract_hhmm(value: str) -> str | None:
    text = str(value or "").strip()
    if len(text) >= 16 and text[10] in {"T", " "}:
        return text[11:16]
    if len(text) >= 5 and text[2] == ":":
        return text[:5]
    return None


def _normalize_format(value: Any) -> str:
    text = str(value or "").strip().lower()
    aliases = {
        "reels": "reel",
        "stories": "story",
        "carrossel": "carousel",
        "carrousel": "carousel",
        "post": "image",
        "feed": "image",
    }
    return aliases.get(text, text)


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _dedupe(values: list[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = str(value or "").strip()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered
