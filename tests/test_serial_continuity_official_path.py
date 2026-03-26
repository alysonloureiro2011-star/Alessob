import unittest

from ace_next.creative_planner import build_creative_plan


class SerialContinuityOfficialPathTest(unittest.TestCase):
    def test_serial_continuity_and_distribution_are_official(self):
        plan = build_creative_plan(
            "clareza soberana",
            recent_memory=[
                {
                    "episode_id": "ep_001",
                    "series_name": "Liberta a Verdade",
                    "headline": "clareza soberana",
                }
            ],
        )
        payload = plan.to_dict()

        self.assertIn("serial_continuity", payload)
        self.assertIn("distribution_context", payload)
        self.assertTrue(isinstance(payload["serial_continuity"], dict))
        self.assertTrue(isinstance(payload["distribution_context"], dict))
        self.assertIn("recommended_next_format", payload["distribution_context"])
        self.assertIn("recommended_next_series_action", payload["distribution_context"])


if __name__ == "__main__":
    unittest.main()
