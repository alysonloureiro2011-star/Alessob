from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ReleaseSurfaceContract:
    release_surface: bool
    runtime_surface: str
    brand_surface_mode: str | None
    token_present: bool
    ig_id_present: bool
    enable_real_publish: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_release_surface_contract(snapshot: dict[str, Any] | None = None) -> ReleaseSurfaceContract:
    snapshot = dict(snapshot or {})
    return ReleaseSurfaceContract(
        release_surface=True,
        runtime_surface="official_runtime_surface",
        brand_surface_mode=snapshot.get("brand_surface_mode"),
        token_present=bool(snapshot.get("token_present")),
        ig_id_present=bool(snapshot.get("ig_id_present")),
        enable_real_publish=bool(snapshot.get("enable_real_publish")),
    )
