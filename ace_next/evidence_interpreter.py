from __future__ import annotations

from typing import Any


REAL_METRIC_FIELDS = (
    "impressions",
    "reach",
    "likes",
    "comments",
    "saves",
    "shares",
)


def _count_real_metrics(real_metrics: dict[str, Any]) -> int:
    return sum(1 for key in REAL_METRIC_FIELDS if real_metrics.get(key) is not None)


def _bridge_state(
    *,
    has_receipt: bool,
    has_media_id: bool,
    has_permalink: bool,
    has_real_metrics: bool,
) -> str:
    if has_real_metrics:
        return "real_metrics_ready"
    if has_receipt and has_media_id and has_permalink:
        return "receipt_with_permalink"
    if has_receipt and has_media_id:
        return "receipt_with_media_id"
    if has_receipt:
        return "receipt_linked"
    return "no_receipt"


def build_evidence_interpreter(*, record: dict[str, Any]) -> dict[str, Any]:
    publish_result = dict(record.get("publish_result") or record.get("receipt") or {})
    real_metrics = dict(record.get("real_metrics") or {})
    performance_ingest = dict(record.get("performance_ingest") or {})

    has_receipt = bool(publish_result.get("receipt_id"))
    has_media_id = bool(publish_result.get("media_id"))
    has_permalink = bool(publish_result.get("permalink"))

    source_status = str(real_metrics.get("source_status") or "not_available_yet")
    has_real_metrics = source_status in {"collected", "partial_collected"}
    metric_count = _count_real_metrics(real_metrics)
    ingest_attempted = bool(performance_ingest.get("attempted"))

    evidence_state = "no_receipt"
    evidence_strength = "none"
    evidence_ready_for_resolution = False
    evidence_reasons: list[str] = []

    bridge_state = _bridge_state(
        has_receipt=has_receipt,
        has_media_id=has_media_id,
        has_permalink=has_permalink,
        has_real_metrics=has_real_metrics,
    )

    if source_status == "ingest_error":
        evidence_state = "ingest_error"
        evidence_strength = "none"
        evidence_reasons.append("houve erro real de ingestão")
    elif not has_receipt:
        evidence_state = "no_receipt"
        evidence_strength = "none"
        evidence_reasons.append("ainda não existe receipt real")
    elif has_receipt and not has_media_id:
        evidence_state = "receipt_only"
        evidence_strength = "low"
        evidence_reasons.append("há receipt, mas ainda não existe media_id real")
    elif has_media_id and not ingest_attempted:
        evidence_state = "linked_real_target"
        evidence_strength = "low"
        evidence_reasons.append("há target real ligado, mas a ingestão ainda não foi tentada")
    elif source_status == "not_available_yet":
        evidence_state = "metrics_pending"
        evidence_strength = "low"
        evidence_reasons.append("há target real, mas as métricas ainda não estão disponíveis")
    elif source_status == "not_supported_for_content_type":
        evidence_state = "weak_evidence"
        evidence_strength = "low"
        evidence_reasons.append("o content_type atual não suportou a métrica desejada")
    elif has_real_metrics:
        if metric_count >= 4:
            evidence_state = "sufficient_evidence"
            evidence_strength = "strong" if metric_count >= 5 else "moderate"
            evidence_ready_for_resolution = True
            evidence_reasons.append("há métricas reais suficientes para leitura conservadora")
        else:
            evidence_state = "weak_evidence"
            evidence_strength = "moderate" if metric_count >= 2 else "low"
            evidence_ready_for_resolution = False
            evidence_reasons.append("há sinal real, mas ainda insuficiente para resolução")
    else:
        evidence_state = "metrics_pending"
        evidence_strength = "low"
        evidence_reasons.append("a evidência real ainda não amadureceu")

    if has_receipt:
        evidence_reasons.append("receipt real presente")
    if has_media_id:
        evidence_reasons.append("media_id real presente")
    if has_permalink:
        evidence_reasons.append("permalink real presente")
    if has_real_metrics:
        evidence_reasons.append(f"{metric_count} métricas reais utilizáveis encontradas")

    return {
        "ok": True,
        "evidence_state": evidence_state,
        "evidence_strength": evidence_strength,
        "has_real_receipt": has_receipt,
        "has_media_id": has_media_id,
        "has_permalink": has_permalink,
        "has_real_metrics": has_real_metrics,
        "evidence_reasons": evidence_reasons,
        "evidence_ready_for_resolution": evidence_ready_for_resolution,
        "source_status": source_status,
        "metric_count": metric_count,
        "bridge_state": bridge_state,
        "audit": {
            "random_used": False,
            "fake_evidence_used": False,
            "brand_live_allowed": False,
        },
    }
