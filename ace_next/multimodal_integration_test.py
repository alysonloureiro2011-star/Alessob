from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .brand_consistency_validator import evaluate_brand_consistency
from .multimodal_reel_qa import MultimodalReelQA
from .premium_eligibility_protocol import evaluate_premium_eligibility_protocol
from .premium_path_validator import evaluate_premium_path


@dataclass(frozen=True)
class CaseResult:
    case_name: str
    ok: bool
    approved_path: bool
    expected_approved_path: bool
    blocked_by: list[str]
    expected_blocked_by: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MultimodalIntegrationTestSuite:
    def run(self) -> dict[str, Any]:
        cases = [
            self._reel_green_path(),
            self._reel_blocked_path(),
            self._image_green_path(),
        ]
        return {
            "ok": all(case.ok for case in cases),
            "suite_name": "multimodal_integration_test_suite",
            "passed": sum(1 for case in cases if case.ok),
            "failed": sum(1 for case in cases if not case.ok),
            "total": len(cases),
            "results": [case.to_dict() for case in cases],
            "runtime_touched": False,
        }

    def _reel_green_path(self) -> CaseResult:
        payload = self._payload()
        pep = evaluate_premium_eligibility_protocol(
            creative_plan=payload["creative_plan"],
            editorial_qa=payload["editorial_qa"],
            visual_qa=payload["visual_qa"],
            perceptual_qa=payload["perceptual_qa"],
            rubric_engine=payload["rubric_engine"],
            brand_veto_gate=payload["brand_veto_gate"],
            publication_authorization_gate={"selected_state": "editorial_staging"},
        )
        brand = evaluate_brand_consistency(
            creative_plan=payload["creative_plan"],
            rubric_engine=payload["rubric_engine"],
            brand_veto_gate=payload["brand_veto_gate"],
            premium_eligibility_protocol=pep,
            brand_context=payload["brand_context"],
            serial_continuity=payload["serial_continuity"],
        )
        multimodal = MultimodalReelQA().run(
            visual_gate={"global_visual_score": 8.7},
            audio_gate={"global_audio_score": 8.6},
            reel_gate={"global_score": 8.8},
            naturalism={"naturalism_state": "naturalism_engine_ready"},
        )
        path = evaluate_premium_path(
            premium_eligibility_protocol=pep,
            publication_authorization_gate={"selected_state": "editorial_staging"},
            brand_consistency_validator=brand,
            multimodal_reel_qa=multimodal,
            format_hint="reel",
        )
        return self._case(
            case_name="reel_green_path",
            path=path,
            expected_approved_path=True,
            expected_blocked_by=[],
        )

    def _reel_blocked_path(self) -> CaseResult:
        payload = self._payload()
        pep = evaluate_premium_eligibility_protocol(
            creative_plan=payload["creative_plan"],
            editorial_qa=payload["editorial_qa"],
            visual_qa=payload["visual_qa"],
            perceptual_qa=payload["perceptual_qa"],
            rubric_engine=payload["rubric_engine"],
            brand_veto_gate=payload["brand_veto_gate"],
            publication_authorization_gate={"selected_state": "editorial_staging"},
        )
        brand = evaluate_brand_consistency(
            creative_plan=payload["creative_plan"],
            rubric_engine=payload["rubric_engine"],
            brand_veto_gate=payload["brand_veto_gate"],
            premium_eligibility_protocol=pep,
            brand_context=payload["brand_context"],
            serial_continuity=payload["serial_continuity"],
        )
        multimodal = MultimodalReelQA().run(
            visual_gate={"global_visual_score": 7.0},
            audio_gate={"global_audio_score": 6.9},
            reel_gate={"global_score": 7.1},
            naturalism={"naturalism_state": "lab"},
        )
        path = evaluate_premium_path(
            premium_eligibility_protocol=pep,
            publication_authorization_gate={"selected_state": "editorial_staging"},
            brand_consistency_validator=brand,
            multimodal_reel_qa=multimodal,
            format_hint="reel",
        )
        return self._case(
            case_name="reel_blocked_path",
            path=path,
            expected_approved_path=False,
            expected_blocked_by=["multimodal_reel_qa"],
        )

    def _image_green_path(self) -> CaseResult:
        payload = self._payload()
        pep = evaluate_premium_eligibility_protocol(
            creative_plan=payload["creative_plan"],
            editorial_qa=payload["editorial_qa"],
            visual_qa=payload["visual_qa"],
            perceptual_qa=payload["perceptual_qa"],
            rubric_engine=payload["rubric_engine"],
            brand_veto_gate=payload["brand_veto_gate"],
            publication_authorization_gate={"selected_state": "editorial_staging"},
        )
        brand = evaluate_brand_consistency(
            creative_plan=payload["creative_plan"],
            rubric_engine=payload["rubric_engine"],
            brand_veto_gate=payload["brand_veto_gate"],
            premium_eligibility_protocol=pep,
            brand_context=payload["brand_context"],
            serial_continuity=payload["serial_continuity"],
        )
        path = evaluate_premium_path(
            premium_eligibility_protocol=pep,
            publication_authorization_gate={"selected_state": "editorial_staging"},
            brand_consistency_validator=brand,
            multimodal_reel_qa={"approved": False},
            format_hint="image",
        )
        return self._case(
            case_name="image_green_path",
            path=path,
            expected_approved_path=True,
            expected_blocked_by=[],
        )

    def _case(
        self,
        *,
        case_name: str,
        path: dict[str, Any],
        expected_approved_path: bool,
        expected_blocked_by: list[str],
    ) -> CaseResult:
        blocked_by = self._normalize(path.get("blocked_by") or [])
        expected_blocked_by = self._normalize(expected_blocked_by)
        approved_path = bool(path.get("approved_path"))
        ok = approved_path == expected_approved_path and blocked_by == expected_blocked_by
        return CaseResult(
            case_name=case_name,
            ok=ok,
            approved_path=approved_path,
            expected_approved_path=expected_approved_path,
            blocked_by=blocked_by,
            expected_blocked_by=expected_blocked_by,
        )

    def _normalize(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for value in values:
            text = str(value).strip()
            if not text or text in seen:
                continue
            seen.add(text)
            ordered.append(text)
        return ordered

    def _payload(self) -> dict[str, Any]:
        return {
            "creative_plan": {
                "topic_seed": "clarity structure focus",
                "headline": "You are not lost. You are operating without structure.",
                "hook": "Without structure, even talent becomes noise.",
                "cta": "Save for later.",
                "body": "Structure reduces noise and improves decision quality.",
            },
            "editorial_qa": {
                "approved": True,
                "breakdown": {
                    "perceived_value": 8.6,
                    "anti_commodity": 8.5,
                    "anti_genericity": 8.4,
                    "naturalism": 8.3,
                    "headline": 8.4,
                    "hook": 8.5,
                    "clarity": 8.6,
                },
            },
            "visual_qa": {"approved": True, "final_score": 86},
            "perceptual_qa": {
                "approved": True,
                "breakdown": {
                    "composition": 8.5,
                    "contrast": 8.6,
                    "legibility": 8.7,
                },
            },
            "rubric_engine": {
                "approved_minimum_quality": True,
                "global_score": 8.8,
                "global_score_100": 88,
                "breakdown": {
                    "brand_fit": 8.8,
                    "authority": 8.4,
                    "anti_genericity": 8.4,
                    "anti_commodity": 8.5,
                    "perceived_value": 8.6,
                    "naturality": 8.3,
                    "headline": 8.4,
                    "hook": 8.5,
                    "clarity": 8.6,
                    "composition": 8.5,
                    "contrast": 8.6,
                    "legibility": 8.7,
                },
            },
            "brand_veto_gate": {"approved": True, "blocked": False},
            "brand_context": {"brand_surface_mode": "protected"},
            "serial_continuity": {
                "series_name": "structural clarity",
                "next_episode_seed": "clarity structure focus",
            },
        }


def run_multimodal_integration_test_suite() -> dict[str, Any]:
    return MultimodalIntegrationTestSuite().run()
