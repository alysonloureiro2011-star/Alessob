from dataclasses import dataclass, asdict
from typing import Any, Dict


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except:
        return default


@dataclass
class SerialResult:
    ok: bool
    mode: str
    is_series: bool
    strategy: str

    def to_dict(self):
        return asdict(self)


class SerialEngine:

    def run(self, *, score: Any = None) -> Dict:
        score = _safe_float(score)

        if score >= 8.8:
            return SerialResult(True, "expansion", True, "repeat_winner").to_dict()

        if score >= 8.0:
            return SerialResult(True, "test", True, "sequence_test").to_dict()

        return SerialResult(True, "single", False, "isolated").to_dict()
