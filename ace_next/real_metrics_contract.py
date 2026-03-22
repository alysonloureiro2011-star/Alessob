from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


@dataclass
class RealMetricsContract:
    impressions: int | None
    reach: int | None
    likes: int | None
    comments: int | None
    saves: int | None
    shares: int | None
    engagement_proxy: float | None
    collected_at: str | None
    source_status: str
    source_reason: str | None
    source_endpoint: str | None
    media_id: str | None
    permalink: str | None
    available_metrics: list[str]
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _to_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _engagement_proxy(
    *,
    likes: int | None,
    comments: int | None,
    saves: int | None,
    shares: int | None,
    reach: int | None,
    impressions: int | None,
) -> float | None:
    denominator = reach or impressions or 0
    if denominator <= 0:
        return None
    interactions = (likes or 0) + (comments or 0) + (saves or 0) + (shares or 0)
    return round(interactions / denominator, 4)


def build_empty_real_metrics(
    *,
    source_status: str,
    source_reason: str,
    media_id: str | None = None,
    permalink: str | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    return RealMetricsContract(
        impressions=None,
        reach=None,
        likes=None,
        comments=None,
        saves=None,
        shares=None,
        engagement_proxy=None,
        collected_at=None,
        source_status=source_status,
        source_reason=source_reason,
        source_endpoint="graph_media_insights",
        media_id=media_id,
        permalink=permalink,
        available_metrics=[],
        errors=list(errors or []),
    ).to_dict()


def build_real_metrics_contract(
    *,
    media_id: str | None,
    permalink: str | None,
    likes: Any = None,
    comments: Any = None,
    impressions: Any = None,
    reach: Any = None,
    saves: Any = None,
    shares: Any = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    likes_i = _to_int(likes)
    comments_i = _to_int(comments)
    impressions_i = _to_int(impressions)
    reach_i = _to_int(reach)
    saves_i = _to_int(saves)
    shares_i = _to_int(shares)

    available_metrics: list[str] = []
    for key, value in {
        "impressions": impressions_i,
        "reach": reach_i,
        "likes": likes_i,
        "comments": comments_i,
        "saves": saves_i,
        "shares": shares_i,
    }.items():
        if value is not None:
            available_metrics.append(key)

    errs = list(errors or [])
    if available_metrics and errs:
        source_status = "partial_collected"
        source_reason = "coleta parcial com dados reais e erros parciais"
    elif available_metrics:
        source_status = "collected"
        source_reason = "dados reais coletados com sucesso"
    elif errs:
        source_status = "collection_error"
        source_reason = "houve erro na coleta e nenhum dado real foi confirmado"
    else:
        source_status = "not_available_yet"
        source_reason = "a coleta ainda não retornou métricas reais"

    return RealMetricsContract(
        impressions=impressions_i,
        reach=reach_i,
        likes=likes_i,
        comments=comments_i,
        saves=saves_i,
        shares=shares_i,
        engagement_proxy=_engagement_proxy(
            likes=likes_i,
            comments=comments_i,
            saves=saves_i,
            shares=shares_i,
            reach=reach_i,
            impressions=impressions_i,
        ),
        collected_at=datetime.utcnow().isoformat() if available_metrics else None,
        source_status=source_status,
        source_reason=source_reason,
        source_endpoint="graph_media_insights",
        media_id=media_id,
        permalink=permalink,
        available_metrics=available_metrics,
        errors=errs,
    ).to_dict()
