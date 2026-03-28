from __future__ import annotations

from typing import Any

from .learning_strategy_bridge import build_learning_strategy_bridge
from .official_runtime import OfficialRuntime as OfficialRuntimeBase
from .performance_store import PerformanceStore


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


class OfficialRuntime(OfficialRuntimeBase):
    """
    Runtime v2 com integração explícita do learning strategy bridge.

    Regra:
    - preserva o runtime oficial atual
    - não quebra contratos existentes
    - injeta guidance de próxima decisão com base no último record persistido
    """

    def _latest_learning_record(self) -> dict[str, Any]:
        try:
            store = PerformanceStore(self.config)
            records = store.list_records(limit=1)
            if not records:
                return {}
            latest = records[-1]
            return dict(latest) if isinstance(latest, dict) else {}
        except Exception:
            return {}

    def _build_learning_strategy_bridge(self) -> dict[str, Any]:
        latest_record = self._latest_learning_record()
        return build_learning_strategy_bridge(latest_record)

    def _apply_learning_strategy(self, result: dict[str, Any]) -> dict[str, Any]:
        result = _safe_dict(result)
        learning_strategy_bridge = self._build_learning_strategy_bridge()
        decision = _safe_dict(learning_strategy_bridge.get("decision"))
        creative_plan = _safe_dict(result.get("creative_plan"))
        performance_summary = _safe_dict(result.get("performance_summary"))
        decision_memory_summary = _safe_dict(result.get("decision_memory_summary"))

        if creative_plan:
            creative_plan["learning_strategy_bridge"] = learning_strategy_bridge
            creative_plan["next_hook_strategy"] = decision.get("next_hook_strategy", "neutral")
            creative_plan["next_format_strategy"] = decision.get("next_format_strategy", "neutral")
            creative_plan["next_style_strategy"] = decision.get("next_style_strategy", "neutral")
            creative_plan["next_timing_strategy"] = decision.get("next_timing_strategy", "neutral")
            result["creative_plan"] = creative_plan

        performance_summary["learning_strategy_bridge_ready"] = bool(learning_strategy_bridge.get("ok", True))
        performance_summary["next_hook_strategy"] = decision.get("next_hook_strategy", "neutral")
        performance_summary["next_format_strategy"] = decision.get("next_format_strategy", "neutral")
        performance_summary["next_style_strategy"] = decision.get("next_style_strategy", "neutral")
        performance_summary["next_timing_strategy"] = decision.get("next_timing_strategy", "neutral")
        result["performance_summary"] = performance_summary

        decision_memory_summary["learning_strategy_bridge"] = learning_strategy_bridge
        result["decision_memory_summary"] = decision_memory_summary

        result["learning_strategy_bridge"] = learning_strategy_bridge
        result["next_cycle_strategy"] = {
            "next_hook_strategy": decision.get("next_hook_strategy", "neutral"),
            "next_format_strategy": decision.get("next_format_strategy", "neutral"),
            "next_style_strategy": decision.get("next_style_strategy", "neutral"),
            "next_timing_strategy": decision.get("next_timing_strategy", "neutral"),
        }
        return result

    def run(
        self,
        *,
        trend: str,
        force_placeholder: bool = False,
        force_real_probe: bool = False,
        probe_state: str | None = None,
    ) -> dict[str, Any]:
        result = super().run(
            trend=trend,
            force_placeholder=force_placeholder,
            force_real_probe=force_real_probe,
            probe_state=probe_state,
        )
        return self._apply_learning_strategy(result)
