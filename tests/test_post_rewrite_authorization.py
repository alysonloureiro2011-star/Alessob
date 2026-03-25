import unittest

from ace_next.brand_veto_gate import evaluate_brand_veto_gate
from ace_next.publication_authorization_gate import authorize_publication
from ace_next.rubric_engine import evaluate_rubric_engine


class PostRewriteAuthorizationTest(unittest.TestCase):
    def test_payload_post_rewrite_enters_authorization_gate(self):
        plan = {
            "problem": "segredo para crescer",
            "insight": "ninguém te conta isso",
            "payoff": "isso muda tudo",
            "cta": "comente aqui",
        }
        editorial_qa = {"breakdown": {"headline": 8.0, "hook": 8.0, "clarity": 8.0, "semantic_density": 8.0, "authority": 8.0, "perceived_value": 8.0, "narrative_tension": 8.0, "anti_generic": 8.0, "anti_commodity": 8.0, "naturalism": 8.0}}
        visual_qa = {"final_score": 82, "hierarchy_gate": {"approved": True, "final_score": 82}, "brand_dignity_score": {"approved": True, "final_score": 82, "breakdown": {"brand_fit": 8.4, "anti_commodity": 8.3, "naturality": 8.2}}}
        perceptual_qa = {"breakdown": {"legibility": 8.0, "contrast": 8.0, "composition": 8.0, "perceived_value_visual": 8.1}}

        rubric = evaluate_rubric_engine(
            plan=plan,
            editorial_qa=editorial_qa,
            visual_qa=visual_qa,
            perceptual_qa=perceptual_qa,
        )
        brand_veto = evaluate_brand_veto_gate(
            plan=plan,
            editorial_qa=editorial_qa,
            visual_qa=visual_qa,
            perceptual_qa=perceptual_qa,
            rubric=rubric,
        )
        result = authorize_publication(
            force_placeholder=False,
            editorial_qa=editorial_qa,
            visual_qa=visual_qa,
            perceptual_qa=perceptual_qa,
            rubric=rubric,
            brand_veto=brand_veto,
        )

        self.assertIn("promotion_readiness_summary", result.to_dict())
        self.assertIn("raw_payload_vs_rewritten_payload", result.to_dict())
        self.assertIn("missing_for_brand_live", result.to_dict())


if __name__ == "__main__":
    unittest.main()
