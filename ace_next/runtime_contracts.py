from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

VALID_PROBE_STATES = {"auto", "internal_lab", "editorial_staging", "brand_live"}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def normalize_trend(value: Any, default: str = "teste real") -> str:
    cleaned = _clean_text(value)
    return cleaned or default


def normalize_probe_state(value: Any, default: str = "auto") -> str:
    cleaned = _clean_text(value).lower()
    if cleaned in VALID_PROBE_STATES:
        return cleaned
    return default


def safe_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if hasattr(value, "to_dict"):
        try:
            parsed = value.to_dict()
            return dict(parsed) if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


@dataclass(frozen=True)
class RuntimeRequest:
    trend: str
    force_placeholder: bool
    force_real_probe: bool
    probe_state: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeExecutionEnvelope:
    request: RuntimeRequest
    source: str = "super_orchestrator"
    mode: str = "official_runtime"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["request"] = self.request.to_dict()
        return data


def build_runtime_request(
    *,
    trend: Any,
    force_placeholder: Any = False,
    force_real_probe: Any = False,
    probe_state: Any = "auto",
) -> RuntimeRequest:
    return RuntimeRequest(
        trend=normalize_trend(trend),
        force_placeholder=safe_bool(force_placeholder, False),
        force_real_probe=safe_bool(force_real_probe, False),
        probe_state=normalize_probe_state(probe_state, "auto"),
    )


def build_runtime_execution_envelope(
    *,
    trend: Any,
    force_placeholder: Any = False,
    force_real_probe: Any = False,
    probe_state: Any = "auto",
    source: str = "super_orchestrator",
    mode: str = "official_runtime",
) -> RuntimeExecutionEnvelope:
    request = build_runtime_request(
        trend=trend,
        force_placeholder=force_placeholder,
        force_real_probe=force_real_probe,
        probe_state=probe_state,
    )
    return RuntimeExecutionEnvelope(request=request, source=source, mode=mode)
