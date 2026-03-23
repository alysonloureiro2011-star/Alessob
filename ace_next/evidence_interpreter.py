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


def _has_real_metrics(real_metrics: dict[str, Any]) -> bool:
    return str(real_metrics.get("source_status") or "") in {"collected", "partial_collected"}


def build_evidence_interpreter(*, record: dict[str, Any]) -> dict[str, Any]:
    publish_result = dict(record.get("publish_result") or record.get("receipt") or {})
    real_metrics = dict(record.get("real_metrics") or {})
    attention_metrics = dict(record.get("attention_metrics") or {})
    performance_ingest = dict(record.get("performance_ingest") or {})

    attention_breakdown = dict(attention_metrics.get("breakdown") or {})
    attention_score = attention_breakdown.get("attention_score")

    has_real_receipt = bool(publish_result.get("receipt_id"))
    has_media_id = bool(publish_result.get("media_id"))
    has_permalink = bool(publish_result.get("permalink"))
    has_real_metrics = _has_real_metrics(real_metrics)

    source_status = str(real_metrics.get("source_status") or "not_available_yet")
    metric_count = _count_real_metrics(real_metrics)
    ingest_attempted = bool(performance_ingest.get("attempted"))

    evidence_state = "no_receipt"
    evidence_strength = "none"
    evidence_ready_for_resolution = False
    evidence_reasons: list[str] = []

    if source_status == "ingest_error":
        evidence_state = "ingest_error"
        evidence_strength = "none"
        evidence_reasons.append("houve erro real de ingestão; não existe base segura para resolução")
    elif not has_real_receipt:
        evidence_state = "no_receipt"
        evidence_strength = "none"
        evidence_reasons.append("ainda não existe receipt real ligado à peça")
    elif has_real_receipt and not has_media_id:
        evidence_state = "receipt_only"
        evidence_strength = "low"
        evidence_reasons.append("há receipt, mas ainda não existe media_id real")
    elif has_media_id and not ingest_attempted:
        evidence_state = "linked_real_target"
        evidence_strength = "low"
        evidence_reasons.append("há alvo real ligado, mas a ingestão ainda não foi tentada")
    elif source_status == "not_available_yet":
        evidence_state = "metrics_pending"
        evidence_strength = "low"
        evidence_reasons.append("a coleta foi tentada, mas ainda não existem métricas reais disponíveis")
    elif source_status == "not_supported_for_content_type":
        evidence_state = "weak_evidence"
        evidence_strength = "low"
        evidence_reasons.append("o content type atual não suportou a leitura desejada de métricas")
    elif has_real_metrics:
        if metric_count >= 4 and (attention_score is not None or has_permalink):
            evidence_state = "sufficient_evidence"
            evidence_strength = "strong" if metric_count >= 5 and attention_score is not None else "moderate"
            evidence_ready_for_resolution = True
            evidence_reasons.append("há métricas reais suficientes para leitura conservadora")
        else:
            evidence_state = "weak_evidence"
            evidence_strength = "moderate" if metric_count >= 2 else "low"
            evidence_ready_for_resolution = metric_count >= 2 and attention_score is not None
            evidence_reasons.append("há algum sinal real, mas ainda insuficiente para uma resolução forte")
    else:
        evidence_state = "metrics_pending"
        evidence_strength = "low"
        evidence_reasons.append("a peça ainda não acumulou evidência real suficiente")

    if has_real_receipt:
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
        "has_real_receipt": has_real_receipt,
        "has_media_id": has_media_id,
        "has_permalink": has_permalink,
        "has_real_metrics": has_real_metrics,
        "evidence_reasons": evidence_reasons,
        "evidence_ready_for_resolution": evidence_ready_for_resolution,
        "source_status": source_status,
        "metric_count": metric_count,
        "audit": {
            "random_used": False,
            "fake_evidence_used": False,
            "pseudo_science_used": False,
        },
    }
