from __future__ import annotations

"""
ACE Ω — Runtime Registry (VERSÃO SOBERANA ALINHADA)

Regra:
- refletir 100% o estado real
- incluir adapters
- zero inconsistência
"""

CURRENT_CAPABILITIES = {

    # =========================
    # PERCEPÇÃO / MISSÃO
    # =========================
    "TrendRadar": {
        "path": "ace_next.trend_radar",
        "symbol": "TrendRadar",
        "status": "active"
    },
    "MissionControl": {
        "path": "ace_next.mission_control",
        "symbol": "decide_mission",
        "status": "active"
    },

    # =========================
    # PLANNER
    # =========================
    "CreativePlannerBridge": {
        "path": "ace_next.creative_planner_runtime_bridge",
        "symbol": "build_creative_plan",
        "status": "active"
    },

    # =========================
    # VISUAL / RENDER
    # =========================
    "VisualPremiumBridge": {
        "path": "ace_next.visual_premium_bridge",
        "symbol": "build_visual_premium_bridge",
        "status": "active"
    },
    "RenderRuntimeBridge": {
        "path": "ace_next.render_runtime_bridge",
        "symbol": "build_render_runtime_bridge",
        "status": "active"
    },

    "VisualHierarchyGate": {
        "path": "ace_next.visual_hierarchy_gate",
        "symbol": "evaluate_visual_hierarchy_gate",
        "status": "active"
    },

    "DignityScore": {
        "path": "ace_next.brand_dignity_score",
        "symbol": "evaluate_brand_dignity_score",
        "status": "active"
    },

    # =========================
    # REEL / ATENÇÃO
    # =========================
    "HookOpeningEngine": {
        "path": "ace_next.hook_opening_engine",
        "symbol": "generate_hook_opening",
        "status": "active"
    },
    "NaturalismEngine": {
        "path": "ace_next.naturalism_engine",
        "symbol": "NaturalismEngine",
        "status": "active"
    },

    # =========================
    # PUBLICAÇÃO
    # =========================
    "PublishRuntimeBridge": {
        "path": "ace_next.publish_runtime_bridge",
        "symbol": "build_publish_runtime_bridge",
        "status": "active"
    },

    # =========================
    # DISTRIBUIÇÃO
    # =========================
    "DistributionTimingEngine": {
        "path": "ace_next.distribution_timing_engine",
        "symbol": "DistributionTimingEngine",
        "status": "active"
    },
    "RecommendationEngine": {
        "path": "ace_next.recommendation_engine",
        "symbol": "RecommendationEngine",
        "status": "active"
    },

    # =========================
    # LEARNING / MEMÓRIA
    # =========================
    "LearningLoop": {
        "path": "ace_next.learning_loop",
        "symbol": "LearningLoop",
        "status": "active"
    },
    "ExperimentRegistry": {
        "path": "ace_next.experiment_registry",
        "symbol": "ExperimentRegistry",
        "status": "active"
    },
    "PerformanceStore": {
        "path": "ace_next.performance_store",
        "symbol": "PerformanceStore",
        "status": "active"
    },

    "ReflectionEngine": {
        "path": "ace_next.reflection_engine",
        "symbol": "ReflectionEngine",
        "status": "active"
    },

    "SerialContinuityEngine": {
        "path": "ace_next.serial_continuity_engine",
        "symbol": "build_serial_continuity",
        "status": "active"
    },

    # =========================
    # GOVERNANÇA
    # =========================
    "SovereignGateBridge": {
        "path": "ace_next.sovereign_gate_bridge",
        "symbol": "build_sovereign_gate_bundle",
        "status": "active"
    },
    "ReleaseAuthority": {
        "path": "ace_next.release_authority",
        "symbol": "ReleaseAuthority",
        "status": "active"
    },

    # =========================
    # ADAPTERS (NOVO BLOCO)
    # =========================
    "ReflectionAdapter": {
        "path": "ace_next.reflection_adapter_runtime",
        "symbol": "run_reflection_adapter",
        "status": "active"
    },

    "SerialAdapter": {
        "path": "ace_next.serial_adapter_runtime",
        "symbol": "run_serial_adapter",
        "status": "active"
    },

    "VisualGateAdapter": {
        "path": "ace_next.visual_gate_adapter_runtime",
        "symbol": "run_visual_gate_adapter",
        "status": "active"
    },

    "DignityAdapter": {
        "path": "ace_next.dignity_adapter_runtime",
        "symbol": "run_dignity_adapter",
        "status": "active"
    },

}


FUTURE_CAPABILITIES = {

    "LLMOrchestrator": {
        "path": "ace_next.llm_orchestrator",
        "symbol": "LLMOrchestrator",
        "status": "not_ready"
    },

    "AceSuperOrchestrator": {
        "path": "ace_next.super_orchestrator",
        "symbol": "AceSuperOrchestrator",
        "status": "not_integrated"
    },

    "SeoSocialEngine": {
        "path": "ace_next.seo_social_engine",
        "symbol": "SeoSocialEngine",
        "status": "missing"
    },

}
