from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .brand_consistency_validator import evaluate_brand_consistency
from .multimodal_reel_qa import MultimodalReelQA
from .premium_eligibility_protocol import evaluate_premium_eligibility_protocol
from .premium_path_validator import evaluate_premium_path


@dataclass(frozen=True)
class BenchmarkResult:
    ok: bool
    benchmark_name: str
    premium_candidate_passed: bool
    weak_candidate_passed: bool
    winner: str
    runtime_touched: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class PremiumPathBenchmark:
    def run(self) -> dict[str, Any]:
        premium_candidate = self._evaluate_candidate(self._premium_payload(), format_hint="reel")
        weak_candidate = self._evaluate_candidate(self._weak_payload(), format_hint="reel")

        premium_passed = bool(premium_candidate.get("approved_path"))
        weak_passed = bool(weak_candidate.get("approved_path"))

        if premium_passed and not weak_passed:
            winner = "premium_candidate"
        elif weak_passed and not premium_passed:
            winner = "weak_candidate"
        elif premium_passed and weak_passed:
            winner = "tie_pass"
        else:
            winner = "tie_fail"

        result = BenchmarkResult(
            ok=premium_passed and not weak_passed,
            benchmark_name="premium_path_benchmark",
            premium_candidate_passed=premium_passed,
            weak_candidate_passed=weak_passed,
            winner=winner,
            runtime_touched=False,
        )
        return {
            **result.to_dict(),
            "premium_candidate": premium_candidate,
            "weak_candidate": weak_candidate,
        }

    def _evaluate_candidate(self, payload: dict[str, Any], *, format_hint: str) -> dict[str, Any]:
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
            visual_gate={"global_visual_score": payload["qa_scores"]["visual"]},
            audio_gate={"global_audio_score": payload["qa_scores"]["audio"]},
            reel_gate={"global_score": payload["qa_scores"]["rhythm"]},
            naturalism={"naturalism_state": payload["qa_scores"]["naturalism_state"]},
        )
        return evaluate_premium_path(
            premium_eligibility_protocol=pep,
            publication_authorization_gate={"selected_state": "editorial_staging"},
            brand_consistency_validator=brand,
            multimodal_reel_qa=multimodal,
            format_hint=format_hint,
        )

    def _premium_payload(self) -> dict[str, Any]:
        return {
            "creative_plan": {
                "topic_seed": "clarity structure focus",
                "headline": "You are not lost. You are operating without structure.",
                "hook": "Without structure, even talent becomes noise.",
                "cta": "Save for later.",
                "body": "Structure reduces noise and improves decision quality.",
            },
            "editorial_qa": {"approved": True, "breakdown": {"perceived_value": 8.6, "anti_commodity": 8.5, "anti_genericity": 8.4, "naturalism": 8.3, "headline": 8.4, "hook": 8.5, "clarity": 8.6}},
            "visual_qa": {"approved": True, "final_score": 86},
            "perceptual_qa": {"approved": True, "breakdown": {"composition": 8.5, "contrast": 8.6, "legibility": 8.7}},
            "rubric_engine": {"approved_minimum_quality": True, "global_score": 8.8, "global_score_100": 88, "breakdown": {"brand_fit": 8.8, "authority": 8.4, "anti_genericity": 8.4, "anti_commodity": 8.5, "perceived_value": 8.6, "naturality": 8.3, "headline": 8.4, "hook": 8.5, "clarity": 8.6, "composition": 8.5, "contrast": 8.6, "legibility": 8.7}},
            "brand_veto_gate": {"approved": True, "blocked": False},
            "brand_context": {"brand_surface_mode": "protected"},
            "serial_continuity": {"series_name": "structural clarity", "next_episode_seed": "clarity structure focus"},
            "qa_scores": {"visual": 8.7, "audio": 8.6, "rhythm": 8.8, "naturalism_state": "naturalism_engine_ready"},
        }

    def _weak_payload(self) -> dict[str, Any]:
        return {
            "creative_plan": {
                "topic_seed": "motivation",
                "headline": "Keep going.",
                "hook": "Do not quit.",
                "cta": "Comment here.",
                "body": "Just keep moving forward.",
            },
            "editorial_qa": {"approved": True, "breakdown": {"perceived_value": 7.5, "anti_commodity": 7.4, "anti_genericity": 7.2, "naturalism": 7.3, "headline": 7.1, "hook": 7.0, "clarity": 7.4}},
            "visual_qa": {"approved": True, "final_score": 76},
            "perceptual_qa": {"approved": True, "breakdown": {"composition": 7.6, "contrast": 7.5, "legibility": 7.8}},
            "rubric_engine": {"approved_minimum_quality": True, "global_score": 7.8, "global_score_100": 78, "breakdown": {"brand_fit": 7.9, "authority": 7.6, "anti_genericity": 7.2, "anti_commodity": 7.4, "perceived_value": 7.5, "naturality": 7.3, "headline": 7.1, "hook": 7.0, "clarity": 7.4, "composition": 7.6, "contrast": 7.5, "legibility": 7.8}},
            "brand_veto_gate": {"approved": True, "blocked": False},
            "brand_context": {"brand_surface_mode": "protected"},
            "serial_continuity": {"series_name": "structural clarity", "next_episode_seed": "focus system"},
            "qa_scores": {"visual": 7.0, "audio": 6.9, "rhythm": 7.1, "naturalism_state": "lab"},
        }


def run_premium_path_benchmark() -> dict[str, Any]:
    return PremiumPathBenchmark().run()
