from __future__ import annotations

from dataclasses import asdict, dataclass
from importlib import import_module
from typing import Any


@dataclass(frozen=True)
class CapabilitySpec:
    name: str
    module_path: str
    symbol: str
    required: bool = False
    stage: str = "current"
    fallback: str | None = None
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


CURRENT_CAPABILITIES: tuple[CapabilitySpec, ...] = (
    CapabilitySpec("load_instagram_auth", ".auth_store", "load_instagram_auth", required=True, stage="wave1"),
    CapabilitySpec("sync_instagram_token_sources", ".auth_store", "sync_instagram_token_sources", required=True, stage="wave1"),
    CapabilitySpec("resolve_brand_surface_policy", ".brand_surface_isolation", "resolve_brand_surface_policy", required=True, stage="wave5"),
    CapabilitySpec("build_creative_plan", ".creative_planner_runtime_bridge", "build_creative_plan", required=True, stage="wave2", notes="runtime bridge wires mission and performance context into soberano planner"),
    CapabilitySpec("evaluate_editorial_quality", ".editorial_rubric", "evaluate_editorial_quality", required=True, stage="wave2"),
    CapabilitySpec("resolve_lab_probe_policy", ".lab_probe_policy", "resolve_lab_probe_policy", required=True, stage="wave5"),
    CapabilitySpec("decide_mission", ".mission_control", "decide_mission", required=True, stage="wave2"),
    CapabilitySpec("evaluate_perceptual_quality", ".perceptual_qa", "evaluate_perceptual_quality", required=True, stage="wave3"),
    CapabilitySpec("PublishService", ".publish_runtime_bridge", "PublishService", required=True, stage="wave5", notes="official publish bridge -> official_instagram_publish with legacy receipt compatibility"),
    CapabilitySpec("persist_instagram_token_to_render", ".render_env_sync", "persist_instagram_token_to_render", required=False, stage="wave5"),
    CapabilitySpec("refresh_instagram_long_lived_token", ".token_upgrade", "refresh_instagram_long_lived_token", required=False, stage="wave5"),
    CapabilitySpec("build_visual_contract", ".visual_contract", "build_visual_contract", required=True, stage="wave3"),
    CapabilitySpec("build_carousel_sequence", ".visual_foundation_pack", "build_carousel_sequence", required=False, stage="wave3"),
    CapabilitySpec("build_stories_sequence", ".visual_foundation_pack", "build_stories_sequence", required=False, stage="wave3"),
    CapabilitySpec("build_typography_spec", ".visual_foundation_pack", "build_typography_spec", required=True, stage="wave3"),
    CapabilitySpec("build_visual_identity", ".visual_foundation_pack", "build_visual_identity", required=True, stage="wave3"),
    CapabilitySpec("evaluate_visual_quality", ".visual_foundation_pack", "evaluate_visual_quality", required=True, stage="wave3"),
    CapabilitySpec("render_visual_foundation_card", ".render_runtime_bridge", "render_visual_foundation_card", required=False, stage="wave3", notes="premium-first render bridge with safe fallback to legacy foundation card"),
    CapabilitySpec("build_visual_premium_bridge", ".visual_premium_bridge", "build_visual_premium_bridge", required=False, stage="wave3"),
    CapabilitySpec("resolve_visual_template", ".visual_templates", "resolve_visual_template", required=False, stage="wave3"),
    CapabilitySpec("evaluate_rubric_engine", ".rubric_engine", "evaluate_rubric_engine", required=False, stage="wave5"),
    CapabilitySpec("evaluate_brand_veto_gate", ".brand_veto_gate", "evaluate_brand_veto_gate", required=False, stage="wave5"),
    CapabilitySpec("authorize_publication", ".publication_authorization_gate", "authorize_publication", required=False, stage="wave5"),
    CapabilitySpec("PerformanceStore", ".performance_store", "PerformanceStore", required=False, stage="wave6"),
    CapabilitySpec("generate_hook_opening", ".hook_opening_engine", "generate_hook_opening", required=False, stage="wave4"),
    CapabilitySpec("ReelStoryboardEngine", ".reel_storyboard_engine", "ReelStoryboardEngine", required=False, stage="wave4"),
    CapabilitySpec("ReelRhythmEngine", ".reel_rhythm_engine", "ReelRhythmEngine", required=False, stage="wave4"),
    CapabilitySpec("PostProductionPipeline", ".post_production_pipeline", "PostProductionPipeline", required=False, stage="wave4"),
    CapabilitySpec("AudioDirectionLayer", ".audio_direction_layer", "AudioDirectionLayer", required=False, stage="wave4"),
    CapabilitySpec("MultimodalReelQA", ".multimodal_reel_qa", "MultimodalReelQA", required=False, stage="wave4"),
    CapabilitySpec("CinematicGate", ".cinematic_gate", "CinematicGate", required=False, stage="wave4"),
    CapabilitySpec("NaturalismEngine", ".naturalism_engine", "NaturalismEngine", required=False, stage="wave4", notes="contract-driven naturalism engine already hardened in main"),
    CapabilitySpec("ReleaseAuthority", ".release_authority", "ReleaseAuthority", required=False, stage="wave4"),
    CapabilitySpec("PublishGuard", ".publish_guard", "PublishGuard", required=False, stage="wave4"),
)


FUTURE_CAPABILITIES: tuple[CapabilitySpec, ...] = (
    CapabilitySpec("TrendRadar", ".trend_radar", "TrendRadar", required=False, stage="future", notes="onda 2"),
    CapabilitySpec("EditorialBrainV2", ".editorial_brain_v2", "EditorialBrainV2", required=False, stage="future", notes="onda 2"),
    CapabilitySpec("AceSuperOrchestrator", ".super_orchestrator", "AceSuperOrchestrator", required=False, stage="future", notes="onda 1/2"),
    CapabilitySpec("ReflectionEngine", ".reflection_engine", "ReflectionEngine", required=False, stage="future", notes="onda 6"),
    CapabilitySpec("SerialContinuityEngine", ".serial_continuity_engine", "SerialContinuityEngine", required=False, stage="future", notes="onda 2/6"),
    CapabilitySpec("DistributionTimingEngine", ".distribution_timing_engine", "DistributionTimingEngine", required=False, stage="future", notes="onda 6"),
    CapabilitySpec("SeoSocialEngine", ".seo_social_engine", "SeoSocialEngine", required=False, stage="future", notes="onda 6"),
    CapabilitySpec("ThompsonSampler", ".thompson_sampler", "ThompsonSampler", required=False, stage="future", notes="onda 6"),
    CapabilitySpec("ExperimentRegistry", ".experiment_registry", "ExperimentRegistry", required=False, stage="future", notes="onda 6"),
    CapabilitySpec("RecommendationEngine", ".recommendation_engine", "RecommendationEngine", required=False, stage="future", notes="onda 6"),
    CapabilitySpec("DignityScore", ".dignity_score", "DignityScore", required=False, stage="future", notes="onda 3"),
    CapabilitySpec("VisualHierarchyGate", ".visual_hierarchy_gate", "VisualHierarchyGate", required=False, stage="future", notes="onda 3"),
    CapabilitySpec("YouTubeAdapter", ".platform_adapters.youtube", "YouTubeAdapter", required=False, stage="future", notes="onda 6"),
    CapabilitySpec("TikTokAdapter", ".platform_adapters.tiktok", "TikTokAdapter", required=False, stage="future", notes="onda 6"),
    CapabilitySpec("ThreadsAdapter", ".platform_adapters.threads", "ThreadsAdapter", required=False, stage="future", notes="onda 6"),
    CapabilitySpec("LLMOrchestrator", ".llm_orchestrator", "LLMOrchestrator", required=False, stage="future", notes="onda 2/6"),
)


ALL_CAPABILITIES: tuple[CapabilitySpec, ...] = CURRENT_CAPABILITIES + FUTURE_CAPABILITIES


def iter_capabilities(include_future: bool = True) -> tuple[CapabilitySpec, ...]:
    return ALL_CAPABILITIES if include_future else CURRENT_CAPABILITIES


def capability_names(include_future: bool = True) -> list[str]:
    return [spec.name for spec in iter_capabilities(include_future=include_future)]


def capability_registry_snapshot(include_future: bool = True) -> dict[str, Any]:
    return {
        "ok": True,
        "total": len(iter_capabilities(include_future=include_future)),
        "current_total": len(CURRENT_CAPABILITIES),
        "future_total": len(FUTURE_CAPABILITIES),
        "capabilities": [spec.to_dict() for spec in iter_capabilities(include_future=include_future)],
    }


def resolve_capability(name: str, package: str = "ace_next") -> dict[str, Any]:
    spec = next((item for item in ALL_CAPABILITIES if item.name == name), None)
    if spec is None:
        return {
            "ok": False,
            "name": name,
            "error": "capability_not_registered",
        }

    try:
        module = import_module(spec.module_path, package=package)
        symbol = getattr(module, spec.symbol)
        return {
            "ok": True,
            "name": spec.name,
            "symbol": symbol,
            "module_path": spec.module_path,
            "required": spec.required,
            "stage": spec.stage,
            "fallback": spec.fallback,
            "notes": spec.notes,
        }
    except Exception as exc:
        return {
            "ok": False,
            "name": spec.name,
            "module_path": spec.module_path,
            "required": spec.required,
            "stage": spec.stage,
            "fallback": spec.fallback,
            "notes": spec.notes,
            "error": f"{type(exc).__name__}: {exc}",
        }


def resolve_many(names: list[str], package: str = "ace_next") -> dict[str, Any]:
    resolved = {name: resolve_capability(name, package=package) for name in names}
    return {
        "ok": all(item.get("ok") for item in resolved.values()),
        "resolved": resolved,
    }
