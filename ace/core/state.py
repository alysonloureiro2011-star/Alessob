
from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict

ISO_FMT = "%Y-%m-%dT%H:%M:%S"


def utc_now_iso() -> str:
    return datetime.utcnow().strftime(ISO_FMT)


@dataclass
class ACEStateRecord:
    mode: str = "BOOTING"
    symbiosis_level: float = 0.0
    instagram_connected: bool = False
    last_action_at: str = ""
    last_cycle_at: str = ""
    last_error: str = ""
    forced_actions: int = 0
    idle_hits: int = 0
    render_pings: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


DEFAULT_ACE_STATE = ACEStateRecord().to_dict()
ACE_STATE: Dict[str, Any] = deepcopy(DEFAULT_ACE_STATE)


def build_default_state() -> Dict[str, Any]:
    return deepcopy(DEFAULT_ACE_STATE)


def ensure_state(state: Dict[str, Any] | None = None) -> Dict[str, Any]:
    state = state if isinstance(state, dict) else {}
    for key, value in DEFAULT_ACE_STATE.items():
        state.setdefault(key, deepcopy(value))
    return state


def state_snapshot(state: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return deepcopy(ensure_state(state if state is not None else ACE_STATE))


def merge_state(state: Dict[str, Any] | None, **updates: Any) -> Dict[str, Any]:
    current = ensure_state(state if state is not None else ACE_STATE)
    for key, value in updates.items():
        if key == "metadata" and isinstance(value, dict):
            current.setdefault("metadata", {})
            current["metadata"].update(value)
        else:
            current[key] = value
    return current


def set_mode(state: Dict[str, Any] | None, mode: str) -> Dict[str, Any]:
    return merge_state(state, mode=str(mode or "UNKNOWN"))


def mark_action(state: Dict[str, Any] | None, *, mode: str | None = None) -> Dict[str, Any]:
    current = ensure_state(state if state is not None else ACE_STATE)
    current["last_action_at"] = utc_now_iso()
    if mode:
        current["mode"] = str(mode)
    return current


def mark_cycle(state: Dict[str, Any] | None, *, mode: str | None = None) -> Dict[str, Any]:
    current = ensure_state(state if state is not None else ACE_STATE)
    current["last_cycle_at"] = utc_now_iso()
    if mode:
        current["mode"] = str(mode)
    return current


def register_error(state: Dict[str, Any] | None, error: Any) -> Dict[str, Any]:
    current = ensure_state(state if state is not None else ACE_STATE)
    current["last_error"] = str(error or "")[:1800]
    return current


def increment_counter(state: Dict[str, Any] | None, key: str, amount: int = 1) -> Dict[str, Any]:
    current = ensure_state(state if state is not None else ACE_STATE)
    current[key] = int(current.get(key, 0)) + int(amount)
    return current


def reset_state(state: Dict[str, Any] | None = None) -> Dict[str, Any]:
    target = state if isinstance(state, dict) else ACE_STATE
    target.clear()
    target.update(build_default_state())
    return target
