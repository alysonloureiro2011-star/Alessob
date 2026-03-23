from __future__ import annotations

from typing import Any


def build_reflection_memory(*, record: dict[str, Any]) -> dict[str, Any]:
    real_metrics = dict(record.get("real_metrics") or {})
    publish_result = dict(record.get("publish_result") or {})
    probe_context = dict(record.get("probe_context") or {})

    status = str(real_metrics.get("source_status") or "not_available_yet")
    notes: list[str] = []

    if publish_result.get("media_id"):
        notes.append(f"media_id real presente: {publish_result.get('media_id')}")
    else:
        notes.append("a peça ainda não possui media_id real confirmado")

    if publish_result.get("permalink"):
        notes.append("permalink real disponível")
    else:
        notes.append("permalink real ainda não disponível")

    if probe_context.get("requested"):
        notes.append(f"probe real solicitado para estado: {probe_context.get('requested_state')}")
        if probe_context.get("publish_executed"):
            notes.append("o probe real foi executado")
        else:
            notes.append("o probe real não foi executado")

    if status == "collected":
        notes.append("já existem dados reais de performance para esta peça")
    elif status == "not_available_yet":
        notes.append("a coleta ainda não retornou dados reais utilizáveis")
    elif status == "ingest_error":
        notes.append("houve erro de ingestão de métricas reais")
        reason = real_metrics.get("source_reason")
        if reason:
            notes.append(str(reason))
    elif status == "not_supported_for_content_type":
        notes.append("o tipo de conteúdo atual não suportou a coleta de métricas desejadas")
    else:
        notes.append("estado de métricas ainda indefinido")

    return {
        "ok": True,
        "status": status,
        "notes": notes,
        "guardrails": {
            "can_change_brand_policy": False,
            "can_change_editorial_policy": False,
            "can_change_visual_policy": False,
            "can_authorize_brand_live": False,
            "can_autopublish": False,
        },
    }
