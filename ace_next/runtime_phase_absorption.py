from __future__ import annotations

from typing import Any, Callable

from .decision_memory_engine import (
    build_decision_memory_entry,
    build_decision_memory_summary,
)
from .publish_cycle_bridge import build_publish_cycle_bundle
from .reel_execution_bridge import build_reel_execution_bundle
from .runtime_contracts import safe_dict
from .sovereign_gate_bridge import build_sovereign_gate_bundle


class RuntimePhaseAbsorption:
    """
    Camada única de absorção das fases 4/5/6/7.

    Objetivo:
    - preservar o progresso das phases antigas
    - impedir runtime paralelo
    - permitir integração limpa por composição no official_runtime

    Esta camada NÃO governa o sistema sozinha.
    Ela apenas oferece enriquecimentos opcionais para o runtime soberano.
    """

    # ---------------------------------------------------------
    # PHASE 4 — REEL EXECUTION BUNDLE
    # ---------------------------------------------------------
    def apply_phase4_reel_stack(
        self,
        *,
        trend: str,
        creative_plan: dict[str, Any],
        visual_qa: dict[str, Any],
        perceptual_qa: dict[str, Any],
        publication_authorization_gate: dict[str, Any],
        operational_state: str,
        publish_truth_state: str,
        fallback_runner: Callable[..., dict[str, Any]],
    ) -> dict[str, Any]:
        format_now = str(
            creative_plan.get("publish_format_now")
            or creative_plan.get("strategic_target_format")
            or "image"
        ).strip().lower()

        if format_now != "reel":
            return fallback_runner(
                trend=trend,
                creative_plan=creative_plan,
                visual_qa=visual_qa,
                perceptual_qa=perceptual_qa,
                publication_authorization_gate=publication_authorization_gate,
                operational_state=operational_state,
                publish_truth_state=publish_truth_state,
            )

        priority = "critical" if format_now == "reel" else "high"

        try:
            bundle = build_reel_execution_bundle(
                creative_plan=creative_plan,
                priority=priority,
            )
            bundle_dict = safe_dict(bundle)
            if bundle_dict:
                cinematic_gate = safe_dict(bundle_dict.get("cinematic_gate"))
                approved = bool(cinematic_gate.get("approved"))

                release_authority = {
                    "ok": True,
                    "release_state": "READY" if approved else "BLOCKED_BY_CINEMATIC_GATE",
                    "approved_for_publish": approved,
                    "operation_mode": str(operational_state or "technical_test"),
                }
                publish_guard = {
                    "ok": True,
                    "mode": "ready" if approved else "blocked",
                    "state": "publish_ready" if approved else "publish_blocked",
                    "can_publish": approved,
                    "next_step": "publish" if approved else "improve_reel_quality",
                    "publish_truth_state": publish_truth_state,
                }

                return {
                    "ok": True,
                    "stack_state": "phase_4_reel_stack_active",
                    "reel_task_contract": safe_dict(bundle_dict.get("reel_task_contract")),
                    "reel_task_state": bundle_dict.get("reel_task_state"),
                    "hook_opening": safe_dict(bundle_dict.get("hook_opening")),
                    "storyboard": safe_dict(bundle_dict.get("storyboard")),
                    "rhythm": safe_dict(bundle_dict.get("rhythm")),
                    "subtitles": safe_dict(bundle_dict.get("subtitles")),
                    "audio_direction": safe_dict(bundle_dict.get("audio_direction")),
                    "multimodal_qa": safe_dict(bundle_dict.get("multimodal_qa")),
                    "cinematic_gate": cinematic_gate,
                    "release_authority": release_authority,
                    "publish_guard": publish_guard,
                    "summary": safe_dict(bundle_dict.get("summary")),
                    "study_alignment": safe_dict(bundle_dict.get("study_alignment")),
                }
        except Exception:
            pass

        return fallback_runner(
            trend=trend,
            creative_plan=creative_plan,
            visual_qa=visual_qa,
            perceptual_qa=perceptual_qa,
            publication_authorization_gate=publication_authorization_gate,
            operational_state=operational_state,
            publish_truth_state=publish_truth_state,
        )

    # ---------------------------------------------------------
    # PHASE 5 — SOVEREIGN GATE BUNDLE
    # ---------------------------------------------------------
    def apply_phase5_authorization_stack(
        self,
        *,
        force_placeholder: bool,
        plan_dict: dict[str, Any],
        editorial_qa: dict[str, Any],
        visual_qa: dict[str, Any],
        perceptual_qa: dict[str, Any],
        env_flags: dict[str, Any],
        request_flags: dict[str, Any],
        staging_hardener: dict[str, Any] | None,
        fallback_runner: Callable[..., tuple[dict[str, Any], dict[str, Any], dict[str, Any]]],
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        try:
            gate_bundle = build_sovereign_gate_bundle(
                creative_plan=plan_dict,
                editorial_qa=editorial_qa,
                visual_qa=visual_qa,
                perceptual_qa=perceptual_qa,
                env_flags=env_flags,
                request_flags=request_flags,
                staging_hardener=staging_hardener or {},
                force_placeholder=force_placeholder,
            )
            gate_dict = safe_dict(gate_bundle)
            rubric = safe_dict(gate_dict.get("rubric_engine"))
            brand_veto = safe_dict(gate_dict.get("brand_veto_gate"))
            authorization = safe_dict(gate_dict.get("publication_authorization_gate"))

            if rubric and brand_veto and authorization:
                sovereign_gate_state = gate_dict.get("gate_state")
                rubric["sovereign_gate_state"] = sovereign_gate_state
                brand_veto["sovereign_gate_state"] = sovereign_gate_state
                authorization["sovereign_gate_state"] = sovereign_gate_state
                authorization["blocked_by_sovereign_gate"] = bool(gate_dict.get("blocked"))
                authorization["block_reasons"] = (
                    gate_dict.get("block_reasons")
                    or authorization.get("block_reasons")
                    or []
                )
                return rubric, brand_veto, authorization
        except Exception:
            pass

        return fallback_runner(
            force_placeholder=force_placeholder,
            plan_dict=plan_dict,
            editorial_qa=editorial_qa,
            visual_qa=visual_qa,
            perceptual_qa=perceptual_qa,
            env_flags=env_flags,
            request_flags=request_flags,
            staging_hardener=staging_hardener,
        )

    # ---------------------------------------------------------
    # PHASE 6 — PUBLISH CYCLE BUNDLE
    # ---------------------------------------------------------
    def apply_phase6_measurement_summary(
        self,
        *,
        base_measurement: dict[str, Any],
        publish_result: dict[str, Any] | None,
    ) -> dict[str, Any]:
        base = safe_dict(base_measurement)

        try:
            cycle_bundle = build_publish_cycle_bundle(
                publish_result=safe_dict(publish_result),
                post_performance_contract=safe_dict(base.get("post_performance_contract")),
                evidence_interpreter=safe_dict(base.get("evidence_interpreter")),
                recommendation_engine=safe_dict(base.get("recommendation_engine")),
            )
            cycle_dict = safe_dict(cycle_bundle)
            if cycle_dict:
                base["publish_cycle"] = cycle_dict
                base["publish_cycle_state"] = cycle_dict.get("cycle_state")
                base["proof_contract"] = cycle_dict.get("proof")
                base["proof_complete"] = bool(cycle_dict.get("proof_complete"))
                base["first_premium_cycle_validated"] = bool(cycle_dict.get("first_premium_cycle_validated"))
                base["wave11_summary"] = {
                    **safe_dict(base.get("wave11_summary")),
                    "cycle_state": cycle_dict.get("cycle_state"),
                    "proof_complete": bool(cycle_dict.get("proof_complete")),
                    "first_premium_cycle_validated": bool(cycle_dict.get("first_premium_cycle_validated")),
                    "next_best_step": cycle_dict.get("next_best_step"),
                }
                base["performance_summary"] = {
                    **safe_dict(base.get("performance_summary")),
                    "publish_cycle_state": cycle_dict.get("cycle_state"),
                    "proof_complete": bool(cycle_dict.get("proof_complete")),
                    "next_best_step": cycle_dict.get("next_best_step"),
                }
        except Exception:
            pass

        return base

    # ---------------------------------------------------------
    # PHASE 7 — DECISION MEMORY BUNDLE
    # ---------------------------------------------------------
    def _extract_phase7_metrics(self, measurement_summary: dict[str, Any]) -> dict[str, Any]:
        performance_ingest = safe_dict(measurement_summary.get("performance_ingest"))
        real_metrics = safe_dict(performance_ingest.get("real_metrics"))
        attention_metrics = safe_dict(measurement_summary.get("attention_metrics"))
        attention_breakdown = safe_dict(attention_metrics.get("breakdown"))

        return {
            "save_rate": float(real_metrics.get("save_rate") or attention_breakdown.get("save_rate") or 0.0),
            "share_rate": float(real_metrics.get("share_rate") or attention_breakdown.get("share_rate") or 0.0),
            "retention": float(real_metrics.get("retention") or attention_breakdown.get("retention") or 0.0),
            "replay_proxy": float(real_metrics.get("replay_proxy") or attention_breakdown.get("replay_proxy") or 0.0),
        }

    def build_phase7_decision_memory_entries(
        self,
        *,
        creative_plan: dict[str, Any],
        mission_decision: dict[str, Any],
        measurement_summary: dict[str, Any],
        trend: str,
    ) -> list[dict[str, Any]]:
        plan = safe_dict(creative_plan)
        mission = safe_dict(mission_decision)
        metrics = self._extract_phase7_metrics(measurement_summary)

        if not any(float(value or 0.0) > 0.0 for value in metrics.values()):
            return []

        hypothesis = (
            plan.get("hypothesis")
            or safe_dict(mission.get("raw")).get("hypothesis")
            or mission.get("hypothesis")
        )
        content_type = (
            plan.get("publish_format_now")
            or plan.get("strategic_target_format")
            or mission.get("content_type")
        )
        publish_style = plan.get("publish_style") or mission.get("style")
        headline = plan.get("headline")
        hook = plan.get("hook")

        entries: list[dict[str, Any]] = []

        if hook:
            entries.append(build_decision_memory_entry(
                axis="hook",
                candidate=str(hook),
                metrics=metrics,
                hypothesis=hypothesis,
                content_type=content_type,
                trend=trend,
            ))

        if content_type:
            entries.append(build_decision_memory_entry(
                axis="format",
                candidate=str(content_type),
                metrics=metrics,
                hypothesis=hypothesis,
                content_type=content_type,
                trend=trend,
            ))

        if publish_style:
            entries.append(build_decision_memory_entry(
                axis="style",
                candidate=str(publish_style),
                metrics=metrics,
                hypothesis=hypothesis,
                content_type=content_type,
                trend=trend,
            ))

        if headline:
            entries.append(build_decision_memory_entry(
                axis="headline",
                candidate=str(headline),
                metrics=metrics,
                hypothesis=hypothesis,
                content_type=content_type,
                trend=trend,
            ))

        return [safe_dict(item) for item in entries if safe_dict(item)]

    def apply_phase7_decision_memory(
        self,
        *,
        creative_plan: dict[str, Any],
        measurement_summary: dict[str, Any],
    ) -> dict[str, Any]:
        plan = dict(creative_plan)

        try:
            current_entries_raw = measurement_summary.get("decision_memory_entries") or []
            previous_entries_raw = measurement_summary.get("previous_decision_memory_entries") or []

            current_entries = [
                safe_dict(item)
                for item in current_entries_raw
                if isinstance(item, dict) and safe_dict(item)
            ]
            previous_entries = [
                safe_dict(item)
                for item in previous_entries_raw
                if isinstance(item, dict) and safe_dict(item)
            ]
            decision_entries = previous_entries + current_entries

            memory_summary = build_decision_memory_summary(
                entries=decision_entries,
                preferred_axis="hook",
            )

            original_hook = str(plan.get("hook") or "").strip()
            best_hook = memory_summary.get("best_candidate")
            hook_changed = bool(best_hook and best_hook != original_hook)

            if hook_changed:
                plan["hook"] = best_hook
                plan["memory_override"] = True
            else:
                plan["memory_override"] = False

            plan["decision_memory_summary"] = memory_summary
            plan["decision_memory_loaded_count"] = len(decision_entries)
            plan["previous_decision_memory_count"] = len(previous_entries)
            plan["current_decision_memory_count"] = len(current_entries)

        except Exception:
            pass

        return plan


def build_runtime_phase_absorption() -> RuntimePhaseAbsorption:
    return RuntimePhaseAbsorption()
