from __future__ import annotations

from typing import Any

from .official_runtime import OfficialRuntime
from .release_surface_contract import build_release_surface_contract
from .super_orchestrator import AceSuperOrchestrator


class OfficialRuntimeSurface:
    """
    Superfície soberana entre app e runtime.

    Nesta etapa ela não muda o comportamento profundo do runtime.
    Ela cria um ponto único de entrada para, nas próximas ondas,
    desacoplar official_app/official_release_surface do núcleo pesado.
    """

    def __init__(self, config: Any) -> None:
        self.config = config
        self.runtime = OfficialRuntime(config)
        self.orchestrator = AceSuperOrchestrator(config)

    def snapshot(self) -> dict[str, Any]:
        runtime_snapshot = self.runtime.snapshot()
        release_surface = build_release_surface_contract(runtime_snapshot).to_dict()
        runtime_snapshot.setdefault("runtime_surface", "official_runtime_surface")
        runtime_snapshot.setdefault("release_surface", release_surface.get("release_surface"))
        runtime_snapshot.setdefault("release_surface_contract", release_surface)
        return runtime_snapshot

    def compact_runtime_summary(self) -> dict[str, Any]:
        summary = self.runtime.compact_runtime_summary()
        summary.setdefault("runtime_surface", "official_runtime_surface")
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
        result = self.orchestrator.run(
            self.runtime,
            trend=trend,
            force_placeholder=force_placeholder,
            force_real_probe=force_real_probe,
            probe_state=probe_state,
        )
        if isinstance(result, dict):
            result.setdefault("runtime_surface", "official_runtime_surface")
            return result
        return {
            "ok": False,
            "error": "official_runtime_surface_invalid_result",
            "runtime_surface": "official_runtime_surface",
        }
