from __future__ import annotations

from typing import Any

from .official_runtime import OfficialRuntime
from .runtime_cycle_persistence import persist_runtime_cycle


class OfficialRuntimeSurface:
    """
    Superfície passiva soberana.

    Regra:
    - NÃO decide
    - NÃO transforma
    - NÃO interfere

    Apenas delega para o runtime oficial.
    """

    def __init__(self, config: Any) -> None:
        self.config = config
        self.runtime = OfficialRuntime(config)

    def snapshot(self) -> dict[str, Any]:
        return self.runtime.snapshot()

    def compact_runtime_summary(self) -> dict[str, Any]:
        return self.runtime.compact_runtime_summary()

    def probe_readiness_summary(self) -> dict[str, Any]:
        return self.runtime.probe_readiness_summary()

    def quality_gap_summary(self) -> dict[str, Any]:
        return self.runtime.quality_gap_summary()

    def last_publish_compact_summary(self) -> dict[str, Any]:
        return self.runtime.last_publish_compact_summary()

    def sync_instagram_auth(self) -> dict[str, Any]:
        return self.runtime.sync_instagram_auth()

    def _safe_dict(self, value: Any) -> dict[str, Any]:
        return dict(value) if isinstance(value, dict) else {}

    def _feedback_payload(self, feedback_payload: dict[str, Any] | None) -> dict[str, Any]:
        feedback_payload = self._safe_dict(feedback_payload)
        normalized = {
            "real_metrics": self._safe_dict(feedback_payload.get("real_metrics")),
            "attention_metrics": self._safe_dict(feedback_payload.get("attention_metrics")),
            "performance_ingest": self._safe_dict(feedback_payload.get("performance_ingest")),
            "recommendation_engine": self._safe_dict(feedback_payload.get("recommendation_engine")),
            "experiment_resolution": self._safe_dict(feedback_payload.get("experiment_resolution")),
            "experiment_registry": self._safe_dict(feedback_payload.get("experiment_registry")),
            "episodic_performance_memory": self._safe_dict(feedback_payload.get("episodic_performance_memory")),
            "reflection_memory": self._safe_dict(feedback_payload.get("reflection_memory")),
        }
        next_cycle_hook_candidate = feedback_payload.get("next_cycle_hook_candidate")
        if next_cycle_hook_candidate is not None:
            normalized["next_cycle_hook_candidate"] = next_cycle_hook_candidate
        return normalized

    def _merge_feedback(self, result: dict[str, Any], feedback_payload: dict[str, Any] | None) -> dict[str, Any]:
        result = dict(result or {})
        feedback = self._feedback_payload(feedback_payload)
        performance_ingest = self._safe_dict(result.get("performance_ingest"))
        performance_ingest_override = self._safe_dict(feedback.get("performance_ingest"))
        if performance_ingest_override:
            performance_ingest = {**performance_ingest, **performance_ingest_override}

        real_metrics = self._safe_dict(feedback.get("real_metrics"))
        if real_metrics:
            existing_real_metrics = self._safe_dict(performance_ingest.get("real_metrics"))
            performance_ingest["real_metrics"] = {**existing_real_metrics, **real_metrics}
            real_metrics_contract = self._safe_dict(result.get("real_metrics_contract"))
            result["real_metrics_contract"] = {**real_metrics_contract, **real_metrics}

        attention_metrics = self._safe_dict(feedback.get("attention_metrics"))
        if attention_metrics:
            result["attention_metrics"] = {
                **self._safe_dict(result.get("attention_metrics")),
                **attention_metrics,
            }

        for key in (
            "recommendation_engine",
            "experiment_resolution",
            "experiment_registry",
            "episodic_performance_memory",
            "reflection_memory",
        ):
            override = self._safe_dict(feedback.get(key))
            if override:
                result[key] = {**self._safe_dict(result.get(key)), **override}

        if performance_ingest:
            result["performance_ingest"] = performance_ingest

        if feedback.get("next_cycle_hook_candidate") is not None:
            result["next_cycle_hook_candidate"] = feedback.get("next_cycle_hook_candidate")

        return result

    def run(
        self,
        *,
        trend: str,
        force_placeholder: bool = False,
        force_real_probe: bool = False,
        probe_state: str | None = None,
        feedback_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result = self.runtime.run(
            trend=trend,
            force_placeholder=force_placeholder,
            force_real_probe=force_real_probe,
            probe_state=probe_state,
        )
        result = self._merge_feedback(result, feedback_payload)
        persisted = persist_runtime_cycle(self.config, result)
        if isinstance(persisted, dict):
            result["runtime_cycle_persistence"] = persisted
            if persisted.get("performance_store"):
                result["performance_store"] = persisted.get("performance_store")
            if persisted.get("learning_loop"):
                result["learning_loop"] = persisted.get("learning_loop")
        return result
