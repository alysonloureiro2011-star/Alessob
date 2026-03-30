from __future__ import annotations

from typing import Any

from .llm_orchestrator import (
    gemini_generate_text,
    generate_text,
    llm_orchestrator_status,
    openai_generate_text,
)
from .recommendation_engine import build_recommendation_engine
from .serial_continuity_engine import build_serial_continuity
from .thompson_sampler import build_thompson_sampler
from .visual_hierarchy_gate import evaluate_visual_hierarchy_gate


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _safe_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return list(value)
    return []


class SerialContinuityEngine:
    """
    Compat layer para o registry futuro.

    Não substitui o módulo original.
    Apenas expõe o símbolo de classe esperado pelo runtime_registry,
    delegando para a função já auditada build_serial_continuity.
    """

    def run(
        self,
        *,
        creative_plan: dict[str, Any] | None = None,
        recent_memory: list | None = None,
    ) -> dict[str, Any]:
        return build_serial_continuity(
            creative_plan=_safe_dict(creative_plan),
            recent_memory=_safe_list(recent_memory),
        )


class ThompsonSampler:
    """
    Compat layer para o registry futuro.
    """

    def run(
        self,
        *,
        record: dict[str, Any] | None = None,
        reward_prediction: dict[str, Any] | None = None,
        conservative_mode: bool = True,
    ) -> dict[str, Any]:
        return build_thompson_sampler(
            record=_safe_dict(record),
            reward_prediction=_safe_dict(reward_prediction),
            conservative_mode=bool(conservative_mode),
        )


class RecommendationEngine:
    """
    Compat layer para o registry futuro.
    """

    def run(self, **kwargs: Any) -> dict[str, Any]:
        return build_recommendation_engine(**kwargs)


class VisualHierarchyGate:
    """
    Compat layer para o registry futuro.
    """

    def evaluate(self, contract: dict[str, Any] | None = None) -> dict[str, Any]:
        return evaluate_visual_hierarchy_gate(_safe_dict(contract))

    def run(self, contract: dict[str, Any] | None = None) -> dict[str, Any]:
        return self.evaluate(contract)


class LLMOrchestrator:
    """
    Compat layer para o registry futuro.

    Expõe uma superfície de classe estável sem reescrever o orquestrador atual.
    """

    def status(self) -> dict[str, Any]:
        return llm_orchestrator_status()

    def run(self, *, task_type: str, input_data: Any) -> dict[str, Any]:
        return generate_text(task_type, input_data)

    def generate(self, *, task_type: str, input_data: Any) -> dict[str, Any]:
        return self.run(task_type=task_type, input_data=input_data)

    @staticmethod
    def generate_openai(prompt: str, *, model: str | None = None) -> dict[str, Any]:
        return openai_generate_text(prompt, model=model)

    @staticmethod
    def generate_gemini(prompt: str, *, model: str | None = None) -> dict[str, Any]:
        return gemini_generate_text(prompt, model=model)


def future_symbol_compat_snapshot() -> dict[str, Any]:
    return {
        "ok": True,
        "serial_continuity_engine": "ready",
        "thompson_sampler": "ready",
        "recommendation_engine": "ready",
        "visual_hierarchy_gate": "ready",
        "llm_orchestrator": "ready",
        "mode": "compatibility_only",
        "runtime_touched": False,
    }
