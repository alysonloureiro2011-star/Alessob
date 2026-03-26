import unittest

from ace_next.creative_planner import build_creative_plan


class PlannerCaptionGateContractTest(unittest.TestCase):
    def test_planner_exposes_caption_gate_fields(self):
        plan = build_creative_plan("clareza soberana")
        payload = plan.to_dict()

        self.assertIn("caption_gate", payload)
        self.assertIn("caption_gate_score", payload)
        self.assertIn("caption_gate_flags", payload)
        self.assertIn("caption_gate_reasons", payload)
        self.assertIn("caption_gate_result", payload)


if __name__ == "__main__":
    unittest.main()
