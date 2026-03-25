import unittest

from ace_next.episodic_serial_contract import build_episode_memory_contract, classify_continuity
from ace_next.serial_continuity_engine_v1 import build_serial_continuity_engine_v1


class EpisodicSerialContractTest(unittest.TestCase):
    def test_episode_without_continuity(self):
        serial = build_serial_continuity_engine_v1(
            topic_seed="clareza e foco",
            hook="texto",
            angle="ângulo",
            sequel_potential="low",
            memory_context={},
        )
        self.assertIn(serial["continuity_state"], {"no_continuity", "continuity_hypothesis"})

    def test_valid_continuity(self):
        serial = build_serial_continuity_engine_v1(
            topic_seed="clareza e disciplina",
            hook="texto",
            angle="ângulo",
            sequel_potential="high",
            memory_context={
                "ace_content_history": [
                    {
                        "episode_id": "ep_001",
                        "series_name": "Liberta a Verdade",
                        "headline": "clareza e disciplina",
                        "problem": "clareza sem disciplina",
                        "episode_index_hint": 1,
                    }
                ]
            },
        )
        self.assertTrue(serial["linked_series_candidate"])
        self.assertEqual(serial["previous_episode_id"], "ep_001")

    def test_episode_lineage_contract(self):
        record = {
            "record_id": "rec_001",
            "creative_plan": {"topic_seed": "clareza e disciplina"},
        }
        serial = {
            "series_name": "Liberta a Verdade",
            "linked_series_candidate": True,
            "matched_episode_id": "ep_prev",
            "next_episode_seed": "o próximo custo",
            "continuity_reason": "há continuidade real suficiente",
            "continuity_confidence": "high",
            "continuity_source_mode": "memory_confirmed",
        }
        payload = build_episode_memory_contract(record=record, serial_continuity=serial)
        self.assertEqual(payload["previous_episode_id"], "ep_prev")
        self.assertEqual(payload["episode_id"], "rec_001")


if __name__ == "__main__":
    unittest.main()
