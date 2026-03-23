from __future__ import annotations

from typing import Any

import requests

from .real_metrics_contract import build_empty_real_metrics, build_real_metrics_contract


OPTIONAL_INSIGHT_METRICS = {
    "plays": "plays",
    "video_views": "video_views",
    "avg_watch_time": "ig_reels_avg_watch_time",
    "completion_proxy": "reel_video_completion_rate",
}

SUPPORTED_CONTENT_TYPES = {
    "image",
    "video",
    "reel",
    "carousel",
    "carousel_album",
    "story",
    "stories",
}


def _graph_get(config: Any, path: str, *, params: dict[str, Any] | None = None, timeout: int = 45) -> dict[str, Any]:
    token = getattr(config, "ig_token", None)
    if not token:
        return {"ok": False, "error": "IG_TOKEN ausente"}

    graph_base = str(getattr(config, "graph_base_url", "https://graph.facebook.com/v23.0")).rstrip("/")
    url = f"{graph_base}/{path.lstrip('/')}"
    query = dict(params or {})
    query["access_token"] = token

    try:
        response = requests.get(url, params=query, timeout=timeout)
        try:
            body = response.json()
        except Exception:
            body = {"raw": response.text[:4000]}

        if response.status_code >= 400:
            return {
                "ok": False,
                "status_code": response.status_code,
                "error": body,
                "url": url,
            }

        return {
            "ok": True,
            "status_code": response.status_code,
            "data": body,
            "url": url,
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc), "url": url}


def _extract_insight_value(payload: dict[str, Any]) -> int | float | None:
    data = payload.get("data") or {}
    entries = data.get("data") if isinstance(data, dict) else None
    if not entries or not isinstance(entries, list):
        return None
    entry = entries[0] if entries else {}
    values = entry.get("values") if isinstance(entry, dict) else None
    if not values or not isinstance(values, list):
        return None
    first_value = values[0] if values else {}
    if isinstance(first_value, dict):
        return first_value.get("value")
    return None


def _normalize_error_text(response: dict[str, Any]) -> str:
    error = response.get("error")
    if isinstance(error, dict):
        return str(error).lower()
    return str(error or "").lower()


def _looks_not_supported(response: dict[str, Any]) -> bool:
    text = _normalize_error_text(response)
    markers = [
        "not supported",
        "unsupported",
        "invalid metric",
        "does not support",
        "cannot query insights for this media",
    ]
    return any(marker in text for marker in markers)


def _set_source_status(
    metrics: dict[str, Any],
    *,
    source_status: str,
    source_reason: str,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    updated = dict(metrics)
    updated["source_status"] = source_status
    updated["source_reason"] = source_reason
    if errors is not None:
        updated["errors"] = list(errors)
    if source_status != "collected":
        updated["collected_at"] = None
    return updated


def collect_real_performance_metrics(
    *,
    config: Any,
    publish_result: dict[str, Any] | None,
) -> dict[str, Any]:
    receipt = dict(publish_result or {})
    media_id = str(receipt.get("media_id") or "").strip() or None
    permalink = str(receipt.get("permalink") or "").strip() or None
    content_type = str(receipt.get("content_type") or "").strip().lower() or None

    if not receipt:
        real_metrics = build_empty_real_metrics(
            source_status="not_available_yet",
            source_reason="não existe publish_result para ingerir",
        )
        return {
            "ok": True,
            "attempted": False,
            "source_status": real_metrics["source_status"],
            "collection_success": False,
            "real_metrics": real_metrics,
            "attention_inputs": {},
            "errors": [],
            "raw": {},
        }

    if content_type and content_type not in SUPPORTED_CONTENT_TYPES:
        real_metrics = build_empty_real_metrics(
            source_status="not_supported_for_content_type",
            source_reason=f"content_type '{content_type}' não suportado para ingestão real",
            media_id=media_id,
            permalink=permalink,
        )
        return {
            "ok": True,
            "attempted": False,
            "source_status": real_metrics["source_status"],
            "collection_success": False,
            "real_metrics": real_metrics,
            "attention_inputs": {},
            "errors": [],
            "raw": {"receipt": receipt},
        }

    if not media_id:
        real_metrics = build_empty_real_metrics(
            source_status="not_available_yet",
            source_reason="receipt sem media_id; ainda não há alvo real para coleta",
            permalink=permalink,
        )
        return {
            "ok": True,
            "attempted": False,
            "source_status": real_metrics["source_status"],
            "collection_success": False,
            "real_metrics": real_metrics,
            "attention_inputs": {},
            "errors": [],
            "raw": {"receipt": receipt},
        }

    if not getattr(config, "ig_token", None):
        real_metrics = build_empty_real_metrics(
            source_status="ingest_error",
            source_reason="token ausente para coleta real",
            media_id=media_id,
            permalink=permalink,
            errors=["IG_TOKEN ausente"],
        )
        return {
            "ok": False,
            "attempted": False,
            "source_status": real_metrics["source_status"],
            "collection_success": False,
            "real_metrics": real_metrics,
            "attention_inputs": {},
            "errors": list(real_metrics["errors"]),
            "raw": {"receipt": receipt},
        }

    attempted = True
    errors: list[str] = []
    unsupported_hits = 0

    media_info = _graph_get(
        config,
        str(media_id),
        params={"fields": "id,permalink,like_count,comments_count"},
    )
    likes = None
    comments = None
    if media_info.get("ok"):
        data = media_info.get("data") or {}
        permalink = str(data.get("permalink") or permalink or "")
        likes = data.get("like_count")
        comments = data.get("comments_count")
    else:
        errors.append(f"media_info_error: {media_info.get('error')}")

    insight_values: dict[str, Any] = {
        "impressions": None,
        "reach": None,
        "saves": None,
        "shares": None,
    }

    insight_metrics = {
        "impressions": "impressions",
        "reach": "reach",
        "saves": "saved",
        "shares": "shares",
    }

    raw_insights: dict[str, Any] = {}
    for local_key, remote_metric in insight_metrics.items():
        response = _graph_get(
            config,
            f"{media_id}/insights",
            params={"metric": remote_metric},
        )
        raw_insights[local_key] = response
        if response.get("ok"):
            insight_values[local_key] = _extract_insight_value(response)
        else:
            if _looks_not_supported(response):
                unsupported_hits += 1
            else:
                errors.append(f"{local_key}_error: {response.get('error')}")

    optional_inputs: dict[str, Any] = {}
    optional_raw: dict[str, Any] = {}
    optional_metric_errors: list[str] = []
    for local_key, remote_metric in OPTIONAL_INSIGHT_METRICS.items():
        response = _graph_get(
            config,
            f"{media_id}/insights",
            params={"metric": remote_metric},
        )
        optional_raw[local_key] = response
        if response.get("ok"):
            optional_inputs[local_key] = _extract_insight_value(response)
        else:
            optional_metric_errors.append(f"{local_key}_error: {response.get('error')}")

    real_metrics = build_real_metrics_contract(
        media_id=media_id,
        permalink=permalink,
        likes=likes,
        comments=comments,
        impressions=insight_values["impressions"],
        reach=insight_values["reach"],
        saves=insight_values["saves"],
        shares=insight_values["shares"],
        errors=errors,
    )

    available_metrics = list(real_metrics.get("available_metrics") or [])
    if available_metrics:
        real_metrics = _set_source_status(
            real_metrics,
            source_status="collected",
            source_reason="coleta real bem-sucedida para a peça publicada",
            errors=errors,
        )
    elif unsupported_hits >= len(insight_metrics):
        real_metrics = _set_source_status(
            real_metrics,
            source_status="not_supported_for_content_type",
            source_reason="o content_type atual não expôs métricas compatíveis para este probe",
            errors=errors,
        )
    elif errors:
        real_metrics = _set_source_status(
            real_metrics,
            source_status="ingest_error",
            source_reason="a coleta real foi tentada, mas falhou",
            errors=errors,
        )
    else:
        real_metrics = _set_source_status(
            real_metrics,
            source_status="not_available_yet",
            source_reason="a coleta foi tentada, mas as métricas ainda não estão disponíveis",
            errors=errors,
        )

    source_status = str(real_metrics.get("source_status") or "not_available_yet")
    return {
        "ok": source_status in {"collected", "not_available_yet", "not_supported_for_content_type"},
        "attempted": attempted,
        "collection_success": source_status == "collected",
        "source_status": source_status,
        "real_metrics": real_metrics,
        "attention_inputs": optional_inputs,
        "optional_metric_errors": optional_metric_errors,
        "errors": list(real_metrics.get("errors") or []),
        "raw": {
            "receipt": receipt,
            "media_info": media_info,
            "insights": raw_insights,
            "optional_insights": optional_raw,
        },
    }
