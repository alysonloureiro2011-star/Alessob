import unittest

from ace_next.creative_planner import build_creative_plan


class MissionPlannerWiringTest(unittest.TestCase):
    def test_mission_overrides_reach_planner(self):
        plan = build_creative_plan(
            "clareza e disciplina",
            overrides={
                "publish_format_now": "carousel",
                "strategic_target_format": "carousel",
                "goal": "retention",
                "hypothesis": "hook claro aumenta retenção",
                "planner_selected": "mission_control_v1",
            },
            mission_decision={
                "content_type": "carousel",
                "goal": "retention",
                "hypothesis": "hook claro aumenta retenção",
                "planner_selected": "mission_control_v1",
            },
        )

        self.assertEqual(plan.publish_format_now, "carousel")
        self.assertEqual(plan.strategic_target_format, "carousel")
        self.assertEqual(plan.goal, "retention")
        self.assertEqual(plan.hypothesis, "hook claro aumenta retenção")
        self.assertIn("mission_decision_wired=true", plan.notes)


if __name__ == "__main__":
    unittest.main()
