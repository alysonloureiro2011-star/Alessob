from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .premium_eligibility_protocol import evaluate_premium_eligibility_protocol


@dataclass(frozen=True)
class RegressionCaseResult:
    case_name: str
    ok: bool
    expected_classification: str
    observed_classification: str
    expected_next_best_state: str
    observed_next_best_state: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PremiumRegressionSuite:
    """
    Suite determinística de regressão premium.

    Objetivo:
    - validar o comportamento do PEP
    - impedir regressão silenciosa entre lab / staging / candidato a brand_live
    - manter a auditoria fora do runtime soberano
    """

    def run(self) -> dict[str, Any]:
        cases = [
            self._case_blocked_quality(),
            self._case_editorial_staging(),
            self._case_brand_live_candidate(),
        ]
        passed = sum(1 for case in cases if case.ok)
        total = len(cases)
        failed_cases = [case.case_name for case in cases if not case.ok]

        return {
            "ok": passed == total,
            "suite_name": "premium_regression_suite",
            "passed": passed,
            "failed": total - passed,
            "total": total,
            "failed_cases": failed_cases,
            "results": [case.to_dict() for case in cases],
            "runtime_touched": False,
            "autopublish_allowed": False,
        }

    def _case_blocked_quality(self) -> RegressionCaseResult:
        result = evaluate_premium_eligibility_protocol(
            editorial_qa={
                "approved": False,
                "breakdown": {
                    "perceived_value": 7.1,
                    "anti_commodity": 7.4,
                    "anti_genericity": 7.3,
                    "naturalism": 7.2,
                    "headline": 7.0,
                    "hook": 7.1,
                    "clarity": 7.4,
                },
            },
            visual_qa={"approved": False, "final_score": 74},
            perceptual_qa={
                "approved": False,
                "breakdown": {
                    "composition": 7.2,
                    "contrast": 7.3,
                    "legibility": 7.4,
                },
            },
            rubric_engine={
                "approved_minimum_quality": False,
                "global_score": 7.5,
                "global_score_100": 75,
                "breakdown": {"brand_fit": 7.9},
            },
            brand_veto_gate={"approved": True, "blocked": False},
            publication_authorization_gate={"selected_state": "internal_lab"},
        )
        return self._build_case_result(
            case_name="blocked_quality",
            result=result,
            expected_classification="blocked_quality",
            expected_next_best_state="internal_lab",
        )

    def _case_editorial_staging(self) -> RegressionCaseResult:
        result = evaluate_premium_eligibility_protocol(
            editorial_qa={
                "approved": True,
                "breakdown": {
                    "perceived_value": 8.0,
                    "anti_commodity": 8.2,
                    "anti_genericity": 8.1,
                    "naturalism": 8.0,
                    "headline": 8.0,
                    "hook": 8.1,
                    "clarity": 8.2,
                },
            },
            visual_qa={"approved": True, "final_score": 80},
            perceptual_qa={
                "approved": True,
                "breakdown": {
                    "composition": 8.0,
                    "contrast": 8.1,
                    "legibility": 8.3,
                },
            },
            rubric_engine={
                "approved_minimum_quality": True,
                "global_score": 8.2,
                "global_score_100": 82,
                "breakdown": {"brand_fit": 8.5},
            },
            brand_veto_gate={"approved": True, "blocked": False},
            publication_authorization_gate={"selected_state": "editorial_staging"},
        )
        return self._build_case_result(
            case_name="editorial_staging",
            result=result,
            expected_classification="editorial_staging",
            expected_next_best_state="brand_live_candidate",
        )

    def _case_brand_live_candidate(self) -> RegressionCaseResult:
        result = evaluate_premium_eligibility_protocol(
            editorial_qa={
                "approved": True,
                "breakdown": {
                    "perceived_value": 8.7,
                    "anti_commodity": 8.7,
                    "anti_genericity": 8.5,
                    "naturalism": 8.4,
                    "headline": 8.5,
                    "hook": 8.6,
                    "clarity": 8.6,
                },
            },
            visual_qa={"approved": True, "final_score": 86},
            perceptual_qa={
                "approved": True,
                "breakdown": {
                    "composition": 8.6,
                    "contrast": 8.6,
                    "legibility": 8.7,
                },
            },
            rubric_engine={
                "approved_minimum_quality": True,
                "global_score": 8.9,
                "global_score_100": 89,
                "breakdown": {"brand_fit": 8.9},
            },
            brand_veto_gate={"approved": True, "blocked": False},
            publication_authorization_gate={"selected_state": "editorial_staging"},
        )
        return self._build_case_result(
            case_name="brand_live_candidate",
            result=result,
            expected_classification="brand_live_candidate",
            expected_next_best_state="brand_live_candidate",
        )

    def _build_case_result(
        self,
        *,
        case_name: str,
        result: dict[str, Any],
        expected_classification: str,
        expected_next_best_state: str,
    ) -> RegressionCaseResult:
        observed_classification = str(result.get("classification") or "")
        observed_next_best_state = str(result.get("next_best_state") or "")
        ok = (
            observed_classification == expected_classification
            and observed_next_best_state == expected_next_best_state
        )
        return RegressionCaseResult(
            case_name=case_name,
            ok=ok,
            expected_classification=expected_classification,
            observed_classification=observed_classification,
            expected_next_best_state=expected_next_best_state,
            observed_next_best_state=observed_next_best_state,
            summary=str(result.get("summary") or ""),
        )


def run_premium_regression_suite() -> dict[str, Any]:
    return PremiumRegressionSuite().run()
