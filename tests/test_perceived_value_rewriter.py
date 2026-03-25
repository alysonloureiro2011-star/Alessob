import unittest

from ace_next.perceived_value_rewriter import build_perceived_value_rewriter


class PerceivedValueRewriterTest(unittest.TestCase):
    def test_rewriter_returns_authority_payload(self):
        payload = {
            "problem": "mude sua vida com mais foco",
            "insight": "ninguém te conta esse segredo",
            "payoff": "isso muda tudo",
            "cta": "comente aqui agora",
        }
        result = build_perceived_value_rewriter(payload)
        self.assertTrue(result["ok"])
        self.assertIn("authority_payload", result)
        self.assertIn("rewritten_problem", result)
        self.assertIn("rewritten_payoff", result)
        self.assertIn("rewritten_cta", result)

    def test_guardrails_detect_commodity(self):
        payload = {
            "problem": "segredo para viralizar",
            "insight": "acredite em você",
            "payoff": "mude sua vida",
            "cta": "comente aqui",
        }
        result = build_perceived_value_rewriter(payload)
        flags = result["anti_commodity_guardrails"]["flags"]
        self.assertTrue(flags)

    def test_rewriter_changes_fields(self):
        payload = {
            "problem": "segredo de autoridade",
            "insight": "isso muda tudo",
            "payoff": "mude sua vida",
            "cta": "comente aqui",
        }
        result = build_perceived_value_rewriter(payload)
        self.assertGreater(result["raw_payload_vs_rewritten_payload"]["changed_fields_count"], 0)


if __name__ == "__main__":
    unittest.main()
