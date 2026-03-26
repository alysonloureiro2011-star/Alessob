from __future__ import annotations

from typing import Any

from .editorial_brain_v2 import EditorialBrainV2
from .official_runtime import OfficialRuntime
from .reflection_engine import ReflectionEngine
from .release_surface_contract import build_release_surface_contract
from .super_orchestrator import AceSuperOrchestrator
from .trend_radar import TrendRadar


class OfficialRuntimeSurface:
    """
    Superfície soberana entre app e runtime.

    Nesta etapa ela continua conservadora:
    - usa TrendRadar para qualificar a entrada
    - usa EditorialBrainV2 para preparar o plano editorial
    - delega a execução ao runtime oficial existente
    - usa ReflectionEngine só como camada de leitura pós-ciclo

    Resultado:
    a inteligência nova começa a viver fora do runtime pesado.
    """

    def __init__(self, config: Any) -> None:
        self.config = config
        self.runtime = OfficialRuntime(config)
        self.orchestrator = AceSuperOrchestrator(config)
        self.trend_radar = TrendRadar()
        self.editorial_brain = EditorialBrainV2()
        self.reflection_engine = ReflectionEngine()

    def _queue_state(self) -> dict[str, int]:
        if hasattr(self.runtime, "_runtime_queue_state"):
            try:
                return self.runtime._runtime_queue_state()
            except Exception:
                return {"active_jobs": 0, "pending_jobs": 0}
        return {"active_jobs": 0, "pending_jobs": 0}

    def _recent_memory(self, limit: int = 5) -> list[dict[str, Any]]:
        if hasattr(self.runtime, "_recent_episodic_memory_for_planner"):
            try:
                return self.runtime._recent_episodic_memory_for_planner(limit=limit)
            except Exception:
                return []
        return []

    def _brand_context(self) -> dict[str, Any]:
        snapshot = self.runtime.snapshot()
        return {
            "brand_surface_mode": snapshot.get("brand_surface_mode"),
            "brand_live_allowed": False,
        }

    def snapshot(self) -> dict[str, Any]:
        runtime_snapshot = self.runtime.snapshot()
        release_surface = build_release_surface_contract(runtime_snapshot).to_dict()
        runtime_snapshot.setdefault("runtime_surface", "official_runtime_surface")
        runtime_snapshot.setdefault("release_surface", release_surface.get("release_surface"))
        runtime_snapshot.setdefault("release_surface_contract", release_surface)
        runtime_snapshot.setdefault(
            "surface_layers",
            {
                "trend_radar": True,
                "editorial_brain_v2": True,
                "reflection_engine": True,
                "super_orchestrator": True,
            },
        )
        return runtime_snapshot

    def compact_runtime_summary(self) -> dict[str, Any]:
        summary = self.runtime.compact_runtime_summary()
        summary.setdefault("runtime_surface", "official_runtime_surface")
        summary.setdefault(
            "surface_layers",
            {
                "trend_radar": True,
                "editorial_brain_v2": True,
                "reflection_engine": True,
                "super_orchestrator": True,
            },
        )
        return summary

    def probe_readiness_summary(self) -> dict[str, Any]:
        summary = self.runtime.probe_readiness_summary()
        summary.setdefault("runtime_surface", "official_runtime_surface")
        return summary

    def quality_gap_summary(self) -> dict[str, Any]:
        summary = self.runtime.quality_gap_summary()
        summary.setdefault("runtime_surface", "official_runtime_surface")
        return summary

    def last_publish_compact_summary(self) -> dict[str, Any]:
        summary = self.runtime.last_publish_compact_summary()
        summary.setdefault("runtime_surface", "official_runtime_surface")
        return summary

    def sync_instagram_auth(self) -> dict[str, Any]:
        return self.runtime.sync_instagram_auth()

    def run(
        self,
        *,
        trend: str,
        force_placeholder: bool = False,
        force_real_probe: bool = False,
        probe_state: str | None = None,
    ) -> dict[str, Any]:
        radar = self.trend_radar.run(
            trend=trend,
            recent_signal_score=None,
            signal_context={
                "source": "official_runtime_surface",
                "mode": "run",
            },
            source="official_runtime_surface",
        )

        brain = self.editorial_brain.run(
            trend=radar.get("effective_trend"),
            format_hint=None,
            recent_signal_score=None,
            queue_state=self._queue_state(),
            signal_context={
                "source": "official_runtime_surface",
                "signal_strength": radar.get("signal_strength"),
            },
            brand_context=self._brand_context(),
            recent_memory=self._recent_memory(limit=5),
        )

        effective_trend = (
            ((brain.get("creative_plan") or {}).get("topic_seed"))
            or radar.get("effective_trend")
            or trend
        )

        result = self.orchestrator.run(
            self.runtime,
            trend=effective_trend,
            force_placeholder=force_placeholder,
            force_real_probe=force_real_probe,
            probe_state=probe_state,
        )

        if isinstance(result, dict):
            real_metrics = (
                dict(result.get("real_metrics_contract") or {})
                or dict((result.get("performance_ingest") or {}).get("real_metrics") or {})
            )
            recommendation_engine = dict(result.get("recommendation_engine") or {})
            attention_metrics = dict(result.get("attention_metrics") or {})
            reflection_preview = self.reflection_engine.run(
                creative_plan=dict(result.get("creative_plan") or {}) or dict(brain.get("creative_plan") or {}),
                real_metrics=real_metrics,
                recommendation_engine=recommendation_engine,
                attention_metrics=attention_metrics,
            )

            result.setdefault("trend_radar", radar)
            result.setdefault("editorial_brain", brain)
            result.setdefault("reflection_preview", reflection_preview)
            result.setdefault("runtime_surface", "official_runtime_surface")
            result.setdefault(
                "surface_layers",
                {
                    "trend_radar": True,
                    "editorial_brain_v2": True,
                    "reflection_engine": True,
                    "super_orchestrator": True,
                },
            )
            return result

        return {
            "ok": False,
            "error": "official_runtime_surface_invalid_result",
            "runtime_surface": "official_runtime_surface",
            "trend_radar": radar,
            "editorial_brain": brain,
        }
