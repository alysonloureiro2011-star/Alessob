from __future__ import annotations

from importlib import import_module
from typing import Any

from .runtime_registry import CURRENT_CAPABILITIES, FUTURE_CAPABILITIES, CapabilitySpec


def _safe_module_import(module_path: str, package: str) -> dict[str, Any]:
    try:
        module = import_module(module_path, package=package)
        return {
            "ok": True,
            "module": module,
            "module_name": getattr(module, "__name__", None),
            "module_file": getattr(module, "__file__", None),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
            "module": None,
            "module_name": None,
            "module_file": None,
        }


def _capability_reality(spec: CapabilitySpec, package: str) -> dict[str, Any]:
    imported = _safe_module_import(spec.module_path, package)
    symbol_exists = False
    symbol_type = None

    if imported.get("ok"):
        module = imported.get("module")
        symbol = getattr(module, spec.symbol, None)
        symbol_exists = symbol is not None
        if symbol is not None:
            symbol_type = type(symbol).__name__

    status = "registered_but_broken"
    if imported.get("ok") and symbol_exists:
        if spec.stage == "future":
            status = "future_but_importable"
        else:
            status = "current_and_importable"
    elif imported.get("ok") and not symbol_exists:
        status = "module_exists_symbol_missing"

    return {
        "name": spec.name,
        "stage": spec.stage,
        "required": spec.required,
        "module_path": spec.module_path,
        "symbol": spec.symbol,
        "notes": spec.notes,
        "import_ok": bool(imported.get("ok")),
        "symbol_exists": symbol_exists,
        "symbol_type": symbol_type,
        "module_name": imported.get("module_name"),
        "module_file": imported.get("module_file"),
        "status": status,
        "error": imported.get("error"),
    }


def audit_runtime_registry_reality(package: str = "ace_next") -> dict[str, Any]:
    current = [_capability_reality(spec, package) for spec in CURRENT_CAPABILITIES]
    future = [_capability_reality(spec, package) for spec in FUTURE_CAPABILITIES]
    all_rows = current + future

    promotion_candidates = [
        row for row in future
        if row.get("status") == "future_but_importable"
    ]
    broken_rows = [
        row for row in all_rows
        if row.get("status") in {"registered_but_broken", "module_exists_symbol_missing"}
    ]

    return {
        "ok": True,
        "package": package,
        "current_total": len(current),
        "future_total": len(future),
        "promotion_candidate_total": len(promotion_candidates),
        "broken_total": len(broken_rows),
        "promotion_candidates": promotion_candidates,
        "broken_capabilities": broken_rows,
        "current": current,
        "future": future,
        "summary": {
            "current_and_importable": sum(1 for row in all_rows if row.get("status") == "current_and_importable"),
            "future_but_importable": len(promotion_candidates),
            "registered_but_broken": sum(1 for row in all_rows if row.get("status") == "registered_but_broken"),
            "module_exists_symbol_missing": sum(1 for row in all_rows if row.get("status") == "module_exists_symbol_missing"),
        },
        "diagnostic": {
            "registry_truth_outdated": len(promotion_candidates) > 0,
            "safe_next_step": (
                "promote importable future capabilities only after audit review"
                if promotion_candidates
                else "keep registry unchanged until new modules exist de verdade"
            ),
            "touches_runtime": False,
            "creates_parallel_runtime": False,
        },
    }
