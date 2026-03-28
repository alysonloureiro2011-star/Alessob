# ace_next/creative_planner.py

from dataclasses import dataclass
from typing import Dict, Any

# IMPORT DO GATE SOBERANO (JÁ EXISTENTE)
from ace_next.reel_retention_policy import evaluate_reel_retention_policy


@dataclass
class CreativePlan:
    content: Dict[str, Any]
    retention_score: float
    publish_ready: bool
    veto_reasons: list
    lift_targets: list


def build_creative_plan(base_content: Dict[str, Any]) -> CreativePlan:
    """
    Planner soberano com gate de retenção real integrado.
    """

    # =========================
    # 1. EXECUTA AVALIAÇÃO REAL
    # =========================
    evaluation = evaluate_reel_retention_policy(base_content)

    retention_score = evaluation.get("score", 0)
    publish_ready = evaluation.get("publish_ready", False)
    veto_reasons = evaluation.get("veto_reasons", [])
    lift_targets = evaluation.get("lift_targets", [])

    # =========================
    # 2. ENDURECE DECISÃO
    # =========================
    if not publish_ready:
        return CreativePlan(
            content=base_content,
            retention_score=retention_score,
            publish_ready=False,
            veto_reasons=veto_reasons,
            lift_targets=lift_targets
        )

    # =========================
    # 3. CONTEÚDO APROVADO
    # =========================
    return CreativePlan(
        content=base_content,
        retention_score=retention_score,
        publish_ready=True,
        veto_reasons=[],
        lift_targets=[]
    )
