from __future__ import annotations

import tempfile
import unittest

from ace_next.dignity_score import evaluate_dignity
from ace_next.experiment_registry import ExperimentRegistry, build_experiment_record
from ace_next.recommendation_engine import build_recommendation_engine
from ace_next.visual_hierarchy_gate import evaluate_visual_hierarchy_gate


class VisualHierarchyGateTests(unittest.TestCase):
    def test_approves_clean_premium_image_contract(self) -> None:
        result = evaluate_visual_hierarchy_gate(
            {
                "brand_system": {"text_contrast_policy": "high_contrast"},
                "template_spec": {
                    "template_id": "premium_foundation_v1",
                    "premium_tier": True,
                    "html_ready": True,
                    "block_order": ["headline", "hook", "body", "cta"],
                    "strategic_format": "image",
                },
                "layout_payload": {
                    "display_payload": {
                        "format": "image",
                        "headline": "O detalhe que separa clareza de ruído",
                        "hook": "Quase todo mundo tenta dizer tudo ao mesmo tempo.",
                        "body": "Quando a hierarquia respira, a mensagem entra mais rápido e fica mais tempo.",
                        "cta": "salve para revisar",
                        "support_points": ["menos ruído", "mais retenção"],
                    }
                },
                "gate_payload": {"format": "image"},
            }
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["approved"])
        self.assertGreaterEqual(result["final_score"], result["minimum_score"])
        self.assertEqual(result["metrics"]["density_signal"], "medium")
        self.assertEqual(result["metrics"]["format"], "image")

    def test_rejects_dense_and_redundant_contract(self) -> None:
        result = evaluate_visual_hierarchy_gate(
            {
                "brand_system": {},
                "template_spec": {
                    "template_id": "crowded_layout_v1",
                    "premium_tier": False,
                    "html_ready": False,
                    "block_order": [],
                    "strategic_format": "story",
                },
                "layout_payload": {
                    "display_payload": {
                        "format": "story",
                        "headline": "SEGREDO QUE NINGUEM TE CONTA SOBRE CLAREZA OPERACIONAL TOTAL AGORA MESMO!!!",
                        "hook": "NINGUEM TE CONTA ISSO!!! CORRE!!! COMENTE AQUI!!!",
                        "body": "Muito texto repetido muito texto repetido muito texto repetido muito texto repetido muito texto repetido.",
                        "cta": "comente aqui agora porque isso muda tudo imediatamente",
                        "support_points": ["ponto 1", "ponto 2", "ponto 3", "ponto 4"],
                    }
                },
                "gate_payload": {"format": "story"},
            }
        )

        self.assertTrue(result["ok"])
        self.assertFalse(result["approved"])
        self.assertIn("minimum_score", result["failed_floors"])
        self.assertIn("support points em excesso", result["rejection_reasons"])
        self.assertIn("reduzir support points", result["recommendations"])
        self.assertEqual(result["metrics"]["density_signal"], "high")


class DignityScoreTests(unittest.TestCase):
    def test_approves_clean_and_contained_piece(self) -> None:
        result = evaluate_dignity(
            creative_plan={
                "headline": "Disciplina reduz ruído mental",
                "hook": "Quando você limpa a entrada, a decisão fica mais leve.",
                "body": "Clareza não nasce de excesso. Nasce de corte.",
                "cta": "salve para revisar",
            },
            subtitle_package={
                "cues": [
                    {"text": "menos ruído"},
                    {"text": "mais sinal"},
                    {"text": "clareza"},
                ]
            },
            visual_qa={"final_score": 88},
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["approved"])
        self.assertGreaterEqual(result["score"], 7.6)
        self.assertIn("mensagem central clara", result["reasons"])
        self.assertIn("tom contido e limpo", result["reasons"])

    def test_flags_sensationalism_and_readability_loss(self) -> None:
        result = evaluate_dignity(
            creative_plan={
                "headline": "SEGREDO ABSURDO QUE NINGUEM TE CONTA AGORA!!!",
                "hook": "OLHA ISSO!!! ISSO VAI MUDAR TUDO!!!",
                "body": "Excesso de impacto visual tende a baixar dignidade.",
                "cta": "COMENTE AGORA",
            },
            subtitle_package={"cues": [{"text": str(i)} for i in range(15)]},
            visual_qa={"final_score": 61},
        )

        self.assertTrue(result["ok"])
        self.assertFalse(result["approved"])
        self.assertIn("reduzir caixa alta e sensacionalismo visual", result["recommendations"])
        self.assertIn("reduzir densidade de cues e preservar leitura", result["recommendations"])


class RecommendationEngineTests(unittest.TestCase):
    def test_candidate_for_brand_live_stays_under_human_review(self) -> None:
        result = build_recommendation_engine(
            evidence_interpreter={"evidence_state": "metrics_ready", "evidence_strength": "strong"},
            experiment_resolution={"resolution_state": "winner_candidate", "confidence_level": "high"},
            resonance_engine={"resonance_score": 82},
            reward_prediction={"reward_prediction_score": 79},
            attention_metrics={"breakdown": {"attention_score": 67}},
            operational_state="editorial_staging",
            serial_continuity={"linked_series_candidate": True, "series_name": "clareza"},
            distribution_context={
                "recommended_next_format": "reel",
                "recommended_next_angle": "aprofundar payoff",
                "recommended_next_series_action": "continuar",
                "recommended_timing_hypothesis": "janela de save/share",
                "source_mode": "distribution_memory",
            },
            publish_result={"receipt_id": "rcpt_1", "media_id": "mid_1", "permalink": "https://example.com/p/1"},
            real_metrics={"source_status": "collected", "saved": 20, "shares": 14},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["experiment_state"], "candidate_for_brand_live")
        self.assertEqual(result["recommended_action"], "promote_to_editorial_staging_candidate")
        self.assertTrue(result["safe_to_promote_to_editorial_staging"])
        self.assertTrue(result["requires_human_review"])
        self.assertFalse(result["guardrails"]["autopublish_allowed"])
        self.assertEqual(result["recommended_next_series_action"], "abrir próximo episódio coerente com base na linhagem já registrada")

    def test_missing_receipt_keeps_recommendation_conservative(self) -> None:
        result = build_recommendation_engine(
            evidence_interpreter={"evidence_state": "no_receipt"},
            experiment_resolution={"resolution_state": "collecting"},
            resonance_engine={},
            reward_prediction={},
            attention_metrics={"breakdown": {"attention_score": 32}},
            operational_state="internal_lab",
            publish_result={},
            real_metrics={},
        )

        self.assertTrue(result["ok"])
        self.assertEqual(result["experiment_state"], "repeat_probe")
        self.assertEqual(result["recommended_action"], "repeat_probe")
        self.assertTrue(result["safe_to_repeat"])
        self.assertFalse(result["safe_to_promote_to_editorial_staging"])


class _Config:
    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir


class ExperimentRegistryTests(unittest.TestCase):
    def test_build_record_and_summary_keep_experiment_governance(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = ExperimentRegistry(_Config(tmpdir))

            winner_record = build_experiment_record(
                record={
                    "creative_plan": {
                        "topic_seed": "clareza causal",
                        "headline": "clareza corta ruído",
                        "hook": "menos ruído, mais retenção",
                    },
                    "visual_template": {"template_id": "premium_card_v1"},
                    "operational_state": "editorial_staging",
                    "evidence_interpreter": {"evidence_state": "metrics_ready", "evidence_strength": "strong"},
                    "experiment_resolution": {"resolution_state": "resolved_winner", "winner_candidate": True},
                    "recommendation_engine": {"recommended_action": "observe"},
                    "publish_result": {"receipt_id": "r1", "media_id": "m1", "permalink": "https://example.com/p/1"},
                    "real_metrics": {"source_status": "collected"},
                    "attention_metrics": {"breakdown": {"attention_score": 81}},
                    "thompson_sampler": {"posterior_mean": 0.91, "selected_variant": "winner"},
                }
            )
            loser_record = build_experiment_record(
                record={
                    "creative_plan": {
                        "topic_seed": "clareza causal",
                        "headline": "clareza sem payoff",
                        "hook": "mais texto, menos impacto",
                    },
                    "visual_template": {"template_id": "premium_card_v1"},
                    "operational_state": "internal_lab",
                    "evidence_interpreter": {"evidence_state": "metrics_ready", "evidence_strength": "medium"},
                    "experiment_resolution": {"resolution_state": "loser_candidate", "loser_candidate": True},
                    "recommendation_engine": {"recommended_action": "compare_variant"},
                    "publish_result": {"receipt_id": "r2", "media_id": "m2", "permalink": "https://example.com/p/2"},
                    "real_metrics": {"source_status": "collected"},
                    "attention_metrics": {"breakdown": {"attention_score": 44}},
                    "thompson_sampler": {"posterior_mean": 0.52, "selected_variant": "loser"},
                }
            )

            registry.upsert_experiment(winner_record)
            summary = registry.upsert_experiment(loser_record)
            experiments = registry.list_experiments(limit=10)

            self.assertEqual(len(experiments), 2)
            self.assertEqual(summary["total_experiments"], 2)
            self.assertEqual(summary["resolved_experiments"], 2)
            self.assertEqual(summary["experiments_resolved_percent"], 100.0)
            self.assertIsNotNone(summary["winner_confidence"])
            self.assertEqual(experiments[0]["experiment_state"], "resolved_winner")
            self.assertEqual(experiments[1]["experiment_state"], "resolved_loser")
            self.assertEqual(experiments[0]["hypothesis_key"], experiments[1]["hypothesis_key"])
            self.assertTrue(experiments[0]["has_real_receipt"])
            self.assertTrue(experiments[0]["has_media_id"])


if __name__ == "__main__":
    unittest.main()
