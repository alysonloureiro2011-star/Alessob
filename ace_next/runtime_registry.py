from __future__ import annotations

from typing import Any, Dict, Optional

# Importa símbolos reais das novas capacidades.
# Caso algumas implementações sejam stubs, ainda assim o registro apontará para elas.

def resolve_capability(name: str) -> Dict[str, Any]:
    """
    Tenta resolver a capacidade solicitada retornando objeto e status.
    """
    capabilities = {
        # Motores existentes (resumidos, já presentes)
        "TrendRadar": {"symbol": None, "ok": False, "error": "TrendRadar not imported here"},
        # Novos motores oficiais
        "SerialContinuityEngine": {"module": "ace_next.serial_continuity_engine", "symbol": "build_serial_continuity"},
        "ReflectionEngine": {"module": "ace_next.reflection_engine", "symbol": "ReflectionEngine"},
        "LLMOrchestrator": {"module": "ace_next.llm_orchestrator", "symbol": "LLMOrchestrator"},
        "SeoSocialEngine": {"module": "ace_next.seo_social_engine", "symbol": "SeoSocialEngine"},
        "YouTubeAdapter": {"module": "ace_next.youtube_adapter", "symbol": "post_youtube"},
        "TikTokAdapter": {"module": "ace_next.tiktok_adapter", "symbol": "post_tiktok"},
        "ThreadsAdapter": {"module": "ace_next.threads_adapter", "symbol": "post_threads"},
    }

    entry = capabilities.get(name)
    if not entry:
        return {"ok": False, "error": "capability_not_found", "symbol": None}

    module_name = entry.get("module")
    symbol_name = entry.get("symbol")

    try:
        module = __import__(module_name, fromlist=[symbol_name])
        symbol = getattr(module, symbol_name)
        return {"ok": True, "symbol": symbol}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "symbol": None}

def capability_registry_snapshot(include_future: bool = True) -> Dict[str, Any]:
    """
    Gera um snapshot de registro, indicando quais capacidades estão disponíveis.
    """
    current = [
        "SerialContinuityEngine",
        "ReflectionEngine",
        "LLMOrchestrator",
        "SeoSocialEngine",
    ]
    future = [
        "YouTubeAdapter",
        "TikTokAdapter",
        "ThreadsAdapter",
    ]
    return {
        "ok": True,
        "current_total": len(current),
        "future_total": len(future) if include_future else 0,
        "current": current,
        "future": future if include_future else [],
    }
