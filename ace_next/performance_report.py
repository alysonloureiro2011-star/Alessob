from __future__ import annotations

from typing import Any, Dict, List

def generate_performance_report(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Constrói um relatório consolidado de performance a partir do resultado de um ciclo.
    Útil para mostrar na interface do usuário o que funcionou e o que precisa evoluir.
    """
    report: Dict[str, Any] = {
        "ok": True,
        "metrics": {},
        "insights": [],
        "next_steps": [],
    }

    performance_ingest = data.get("performance_ingest") or {}
    recommendation = data.get("recommendation_engine") or {}
    experiment_resolution = data.get("experiment_resolution") or {}
    authorized_payload = (
        (data.get("authorized_payload_resolution") or {}).get("authorized_payload")
        or {}
    )

    # Coletar métricas básicas
    metrics = {
        "real_metrics": performance_ingest.get("real_metrics"),
        "attention_inputs": performance_ingest.get("attention_inputs"),
        "source_status": performance_ingest.get("source_status"),
    }
    report["metrics"] = metrics

    # Inserir insights do recommendation engine
    rec_action = recommendation.get("recommended_action")
    if rec_action:
        report["insights"].append(f"Recomendação de ação: {rec_action}")
        if recommendation.get("next_best_step"):
            report["insights"].append(f"Próximo melhor passo: {recommendation.get('next_best_step')}")

    # Resolver evidências experimentais
    res_state = experiment_resolution.get("resolution_state")
    if res_state:
        report["insights"].append(f"Estado de resolução do experimento: {res_state}")

    # Sugerir próximas ações genéricas
    if not metrics.get("real_metrics"):
        report["next_steps"].append("Realizar uma publicação real para obter métricas.")
    if authorized_payload.get("hook"):
        report["next_steps"].append("Reavaliar a força do hook usando o QualityCalibrationEngine.")
    if rec_action == "publish_or_improve":
        report["next_steps"].append("Aprimorar a peça antes de publicar.")

    return report
