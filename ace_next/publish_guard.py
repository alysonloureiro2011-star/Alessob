from dataclasses import dataclass, asdict
from typing import Any, Dict


def _safe_dict(value: Any) -> Dict:
    return dict(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


@dataclass
class PublishGuardResult:
    ok: bool
    state: str
    mode: str
    can_publish: bool
    next_step: str
    notes: list

    def to_dict(self):
        return asdict(self)


class PublishGuard:

    def run(
        self,
        *,
        release_authority: Dict | None = None,
        publish_truth: Dict | None = None,
    ) -> Dict:
        release_authority = _safe_dict(release_authority)
        publish_truth = _safe_dict(publish_truth)

        release_state = _clean_text(release_authority.get("release_state") or "BLOCKED")
        truth_state = _clean_text(publish_truth.get("truth_state") or "publish_truth_absent")
        approved = bool(release_authority.get("approved_for_publish"))

        if approved and truth_state in {"publish_truth_absent", "publish_attempt_recorded"}:
            mode = "ready"
            can_publish = True
            next_step = "publish_now"
        elif approved and truth_state == "publish_truth_confirmed":
            mode = "done"
            can_publish = False
            next_step = "measure_now"
        else:
            mode = "blocked"
            can_publish = False
            next_step = "improve_quality"

        return PublishGuardResult(
            ok=True,
            state="publish_guard_ready",
            mode=mode,
            can_publish=can_publish,
            next_step=next_step,
            notes=[
                f"release_state={release_state}",
                f"truth_state={truth_state}",
                f"next_step={next_step}",
            ],
        ).to_dict()
