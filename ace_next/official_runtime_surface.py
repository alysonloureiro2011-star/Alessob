from __future__ import annotations

from typing import Any

from .official_runtime import OfficialRuntime


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

    # =============================
    # PROXIES DIRETOS
    # =============================

    def snapshot(self) -> dict:
        return self.runtime.snapshot()

    def compact_runtime_summary(self) -> dict:
        return self.runtime.compact_runtime_summary()

    def probe_readiness_summary(self) -> dict:
        return self.runtime.probe_readiness_summary()

    def quality_gap_summary(self) -> dict:
        return self.runtime.quality_gap_summary()

    def last_publish_compact_summary(self) -> dict:
        return self.runtime.last_publish_compact_summary()

    def sync_instagram_auth(self) -> dict:
        return self.runtime.sync_instagram_auth()

    # =============================
    # EXECUÇÃO CENTRAL
    # =============================

    def run(
        self,
        *,
        trend: str,
        force_placeholder: bool = False,
        force_real_probe: bool = False,
        probe_state: str | None = None,
    ) -> dict:
        """
        Execução única e soberana.

        Toda inteligência está no runtime.
        """
        return self.runtime.run(
            trend=trend,
            force_placeholder=force_placeholder,
            force_real_probe=force_real_probe,
            probe_state=probe_state,
        )
