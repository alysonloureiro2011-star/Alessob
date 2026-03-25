import unittest

from ace_next.experiment_learning_contract import (
    build_evidence_delta,
    build_learning_bridge_contract,
    derive_experiment_state_machine,
)


class ExperimentLearningContractTest(unittest.TestCase):
    def test_experiment_without_receipt(self):
        machine = derive_experiment_state_machine(
            operational_state="internal_lab",
            evidence_state="no_receipt",
            resolution_state="collecting",
            publish_result={},
            evidence_interpreter={"evidence_state": "no_receipt"},
            real_metrics={},
        )
        self.assertEqual(machine["experiment_state"], "repeat_probe")

    def test_receipt_without_media_id(self):
        machine = derive_experiment_state_machine(
            operational_state="internal_lab",
            evidence_state="receipt_only",
            resolution_state="collecting",
            publish_result={"receipt_id": "r1"},
            evidence_interpreter={"evidence_state": "receipt_only"},
            real_metrics={},
        )
        self.assertEqual(machine["experiment_state"], "collecting")

    def test_media_id_without_metrics(self):
        delta = build_evidence_delta(
            publish_result={"receipt_id": "r1", "media_id": "m1"},
            evidence_interpreter={"evidence_state": "receipt_with_media_id"},
            real_metrics={"source_status": "not_available_yet"},
        )
        self.assertEqual(delta["delta_state"], "media_id_without_sufficient_metrics")

    def test_learning_bridge_conservative(self):
        machine = {
            "experiment_state": "hold",
            "operational_state": "editorial_staging",
            "evidence_state": "receipt_with_media_id",
            "resolution_state": "collecting",
            "promotion_readiness": "not_ready",
            "reason_for_repeat": None,
            "reason_not_resolved": "há media_id real, mas ainda não existem métricas suficientes",
        }
        bridge = build_learning_bridge_contract(
            experiment_state_machine=machine,
            recommendation_engine={"recommended_action": "wait_metrics"},
            episodic_memory={"episode_id": "ep_01"},
            serial_continuity={"linked_series_candidate": True},
            distribution_context={"recommended_next_format": "carousel"},
        )
        self.assertFalse(bridge["fake_data_used"])
        self.assertTrue(bridge["episodic_memory_seen"])


if __name__ == "__main__":
    unittest.main()
