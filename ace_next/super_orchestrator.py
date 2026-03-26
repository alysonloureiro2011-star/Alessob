from __future__ import annotations

from typing import Any

from .runtime_contracts import build_runtime_execution_envelope


class AceSuperOrchestrator:
    """
    Camada fina de orquestração soberana.

    Nesta primeira etapa ele não reescreve o runtime.
    Ele normaliza a chamada, registra um envelope único de execução
    e delega a execução ao núcleo oficial já existente.

    Objetivo: congelar a superfície pública do runtime e impedir que
    futuras evoluções espalhem lógica por official_app.py e official_runtime.py.
    """

    def __init__(self, config: Any) -> None:
        self.config = config

    def build_execution_envelope(
        self,
        *,
        trend: Any,
        force_placeholder: Any = False,
        force_real_probe: Any = False,
        probe_state: Any = "auto",
    ) -> dict[str, Any]:
        envelope = build_runtime_execution_envelope(
            trend=trend,
            force_placeholder=force_placeholder,
            force_real_probe=force_real_probe,
            probe_state=probe_state,
            source="super_orchestrator",
            mode="official_runtime",
        )
        return envelope.to_dict()

    def run(
        self,
        runtime: Any,
        *,
        trend: Any,
        force_placeholder: Any = False,
        force_real_probe: Any = False,
        probe_state: Any = "auto",
    ) -> dict[str, Any]:
        envelope = self.build_execution_envelope(
            trend=trend,
            force_placeholder=force_placeholder,
            force_real_probe=force_real_probe,
            probe_state=probe_state,
        )

        if hasattr(runtime, "_run_cycle_internal"):
            result = runtime._run_cycle_internal(
                trend=envelope["request"]["trend"],
                force_placeholder=envelope["request"]["force_placeholder"],
                force_real_probe=envelope["request"]["force_real_probe"],
                probe_state=envelope["request"]["probe_state"],
            )
        else:
            result = runtime.run(
                trend=envelope["request"]["trend"],
                force_placeholder=envelope["request"]["force_placeholder"],
                force_real_probe=envelope["request"]["force_real_probe"],
                probe_state=envelope["request"]["probe_state"],
            )

        if isinstance(result, dict):
            result.setdefault("execution_envelope", envelope)
            result.setdefault("execution_surface", "super_orchestrator")
            return result

        return {
            "ok": False,
            "error": "super_orchestrator_invalid_runtime_result",
            "execution_envelope": envelope,
            "execution_surface": "super_orchestrator",
        }
