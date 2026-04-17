from __future__ import annotations

from typing import Any


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _limit_words(text: str, max_words: int) -> str:
    words = _clean_text(text).split()
    if len(words) <= max_words:
        return " ".join(words)
    return " ".join(words[:max_words]).strip()


class PrePublishRewriteEngine:
    """
    Endurece sem abrir gate:
    - reduz hook/body/cta quando estão ruins
    - aumenta clareza e valor percebido
    - prepara caption/meta para Instagram
    """

    def _infer_targets(
        self,
        *,
        creative_plan: dict[str, Any],
        editorial_qa: dict[str, Any] | None,
    ) -> dict[str, bool]:
        editorial_qa = dict(editorial_qa or {})
        reasons = [str(x).lower() for x in (editorial_qa.get("reasons") or [])]
        flags = [str(x).lower() for x in (editorial_qa.get("flags") or [])]

        hook = _clean_text(creative_plan.get("hook"))
        body = _clean_text(creative_plan.get("body"))
        cta = _clean_text(creative_plan.get("cta"))
        payoff = _clean_text(creative_plan.get("payoff"))

        return {
            "rewrite_hook": len(hook.split()) > 12 or any("hook" in x for x in reasons + flags),
            "rewrite_body": len(body.split()) > 60 or any("body" in x for x in reasons + flags),
            "rewrite_cta": len(cta.split()) < 4 or any("cta" in x for x in reasons + flags),
            "rewrite_payoff": len(payoff.split()) < 5 or any("value" in x or "payoff" in x for x in reasons + flags),
        }

    def _heuristic_rewrite(
        self,
        *,
        creative_plan: dict[str, Any],
        trend: str,
        rewrite_targets: dict[str, bool],
    ) -> dict[str, Any]:
        plan = dict(creative_plan)

        trend_base = _clean_text(plan.get("topic_seed") or trend or "tema")
        headline = _clean_text(plan.get("headline") or trend_base)
        hook = _clean_text(plan.get("hook") or headline or trend_base)
        body = _clean_text(plan.get("body") or "")
        cta = _clean_text(plan.get("cta") or "")
        payoff = _clean_text(plan.get("payoff") or "")

        if rewrite_targets.get("rewrite_hook"):
            plan["hook"] = _limit_words(
                f"O erro escondido por trás de {trend_base}",
                10,
            )

        if rewrite_targets.get("rewrite_body"):
            plan["body"] = _limit_words(
                body
                or f"{trend_base} afeta atenção, decisão e resultado. O ponto central é cortar ruído, elevar clareza e transformar a mensagem em valor percebido imediato.",
                42,
            )

        if rewrite_targets.get("rewrite_cta"):
            plan["cta"] = "Salve e envie para alguém que precisa disto."

        if rewrite_targets.get("rewrite_payoff"):
            plan["payoff"] = _limit_words(
                payoff
                or f"Entender {trend_base} com clareza para agir melhor e evitar perda de atenção, tempo e resultado.",
                18,
            )

        if not _clean_text(plan.get("headline")):
            plan["headline"] = _limit_words(f"{trend_base}: o ponto que quase ninguém vê", 12)

        return plan

    def rewrite(
        self,
        *,
        creative_plan: dict[str, Any],
        trend: str,
        editorial_qa: dict[str, Any] | None = None,
        llm_orchestrator: Any | None = None,
        seo_social_engine: Any | None = None,
        platform: str = "instagram",
    ) -> dict[str, Any]:
        plan = dict(creative_plan or {})
        rewrite_targets = self._infer_targets(
            creative_plan=plan,
            editorial_qa=editorial_qa,
        )

        rewrite_needed = any(rewrite_targets.values())
        applied_by = "none"

        if rewrite_needed and llm_orchestrator and hasattr(llm_orchestrator, "repair_plan"):
            try:
                llm_result = llm_orchestrator.repair_plan(
                    trend=trend,
                    creative_plan=plan,
                    rewrite_targets=rewrite_targets,
                    platform=platform,
                )
                llm_result = dict(llm_result or {})
                repaired = dict(llm_result.get("creative_plan") or {})
                if llm_result.get("ok") and repaired:
                    plan.update(repaired)
                    applied_by = "llm_orchestrator"
            except Exception:
                applied_by = "heuristic_fallback"

        if rewrite_needed and applied_by == "none":
            plan = self._heuristic_rewrite(
                creative_plan=plan,
                trend=trend,
                rewrite_targets=rewrite_targets,
            )
            applied_by = "heuristic_rewrite"

        seo_payload = {}
        if seo_social_engine and hasattr(seo_social_engine, "build_metadata"):
            try:
                seo_payload = dict(
                    seo_social_engine.build_metadata(
                        trend=trend,
                        creative_plan=plan,
                        platform=platform,
                    )
                    or {}
                )
            except Exception:
                seo_payload = {}

        if seo_payload:
            caption = _clean_text(
                seo_payload.get("caption")
                or seo_payload.get("description")
                or plan.get("caption")
                or ""
            )
            hashtags = seo_payload.get("hashtags") or []
            if caption:
                plan["caption"] = caption
            if isinstance(hashtags, list) and hashtags:
                plan["hashtags"] = hashtags[:8]
            plan["seo_social"] = seo_payload

        return {
            "ok": True,
            "rewrite_needed": rewrite_needed,
            "rewrite_applied": rewrite_needed and applied_by != "none",
            "post_rewrite_state": (
                "rewritten_with_llm" if applied_by == "llm_orchestrator"
                else "rewritten_heuristically" if applied_by == "heuristic_rewrite"
                else "no_rewrite_needed"
            ),
            "rewrite_targets": rewrite_targets,
            "applied_by": applied_by,
            "creative_plan": plan,
            "seo_social": seo_payload,
        }
