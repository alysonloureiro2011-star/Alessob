from __future__ import annotations

from typing import Any

from .runtime_registry import capability_registry_snapshot, resolve_capability


def bootstrap_capabilities() -> dict[str, Any]:
    snapshot = capability_registry_snapshot(include_future=False)
    resolved = {}

    for item in snapshot.get("capabilities", []):
        name = item.get("name")
        if not name:
            continue
        resolved[name] = resolve_capability(name)

    return {
        "ok": True,
        "registry": snapshot,
        "resolved": resolved,
        "loaded": [name for name, meta in resolved.items() if meta.get("ok")],
        "failed": [name for name, meta in resolved.items() if not meta.get("ok")],
    }


def bootstrap_healthcheck() -> dict[str, Any]:
    boot = bootstrap_capabilities()
    return {
        "ok": boot.get("ok"),
        "total": boot.get("registry", {}).get("current_total"),
        "loaded": len(boot.get("loaded", [])),
        "failed": len(boot.get("failed", [])),
        "failed_items": boot.get("failed"),
    }
