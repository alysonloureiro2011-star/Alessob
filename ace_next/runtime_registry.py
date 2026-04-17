from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import importlib
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CapabilitySpec:
    name: str
    tier: str
    preferred: tuple[tuple[str, str], ...]
    aliases: tuple[str, ...] = ()
    notes: str = ""


def _module_path(relative_module: str) -> str:
    relative_module = str(relative_module or "").strip()
    if not relative_module:
        return ""
    if relative_module.startswith("ace_next."):
        return relative_module
    if relative_module.startswith("."):
        return f"ace_next{relative_module}"
    return f"ace_next.{relative_module}"


def _safe_import(module_path: str):
    try:
        return importlib.import_module(module_path)
    except Exception:
        return None


@lru_cache(maxsize=1)
def _discover_local_modules() -> tuple[str, ...]:
    root = Path(__file__).resolve().parent
    modules: list[str] = []

    for path in root.rglob("*.py"):
        if path.name.startswith("__pycache__"):
            continue
        if path.name == "runtime_registry.py":
            continue

        relative = path.relative_to(root).with_suffix("")
        parts = list(relative.parts)

        if parts[-1] == "__init__":
            parts = parts[:-1]

        if not parts:
            continue

        dotted = "ace_next." + ".".join(parts)
        modules.append(dotted)

    modules = sorted(set(modules))
    return tuple(modules)


def _symbol_candidates(spec: CapabilitySpec) -> tuple[str, ...]:
    names: list[str] = []

    for _, attr in spec.preferred:
        if attr and attr not in names:
            names.append(attr)

    if spec.name not in names:
        names.append(spec.name)

    for alias in spec.aliases:
        if alias and alias not in names:
            names.append(alias)

    return tuple(names)


def _try_explicit_paths(spec: CapabilitySpec) -> dict[str, Any] | None:
    errors: list[str] = []

    for relative_module, attr in spec.preferred:
        module_path = _module_path(relative_module)
        module = _safe_import(module_path)
        if module is None:
            errors.append(f"{module_path}: import_failed")
            continue

        if hasattr(module, attr):
            return {
                "ok": True,
                "name": spec.name,
                "tier": spec.tier,
                "symbol": getattr(module, attr),
                "module": module_path,
                "attr": attr,
                "resolution_mode": "explicit",
                "notes": spec.notes,
            }

        errors.append(f"{module_path}: missing_attr:{attr}")

    if errors:
        return {
            "ok": False,
            "name": spec.name,
            "tier": spec.tier,
            "symbol": None,
            "module": None,
            "attr": None,
            "resolution_mode": "explicit_failed",
            "error": "; ".join(errors),
            "notes": spec.notes,
        }

    return None


def _try_dynamic_scan(spec: CapabilitySpec) -> dict[str, Any]:
    symbol_names = _symbol_candidates(spec)
    scan_errors: list[str] = []

    for module_path in _discover_local_modules():
        module = _safe_import(module_path)
        if module is None:
            scan_errors.append(f"{module_path}: import_failed")
            continue

        for attr in symbol_names:
            if hasattr(module, attr):
                return {
                    "ok": True,
                    "name": spec.name,
                    "tier": spec.tier,
                    "symbol": getattr(module, attr),
                    "module": module_path,
                    "attr": attr,
                    "resolution_mode": "dynamic_scan",
                    "notes": spec.notes,
                }

    return {
        "ok": False,
        "name": spec.name,
        "tier": spec.tier,
        "symbol": None,
        "module": None,
        "attr": None,
        "resolution_mode": "dynamic_scan_failed",
        "error": f"symbol_not_found:{spec.name}",
        "searched_attrs": list(symbol_names),
        "notes": spec.notes,
    }


_CAPABILITY_SPECS: tuple[CapabilitySpec, ...] = (
    CapabilitySpec(
        name="sync_instagram_token_sources",
        tier="current",
        preferred=((".auth_store", "sync_instagram_token_sources"),),
    ),
    CapabilitySpec(
        name="load_instagram_auth",
        tier="current",
        preferred=((".auth_store", "load_instagram_auth"),),
    ),
    CapabilitySpec(
        name="refresh_instagram_long_lived_token",
        tier="current",
        preferred=((".auth_store", "refresh_instagram_long_lived_token"),),
    ),
    CapabilitySpec(
        name="persist_instagram_token_to_render",
        tier="current",
        preferred=((".auth_store", "persist_instagram_token_to_render"),),
    ),
    CapabilitySpec(
        name="PublishService",
        tier="current",
        preferred=(
            (".publish_runtime_bridge", "PublishService"),
            (".official_instagram_publish", "OfficialInstagramPublishService"),
        ),
        aliases=("OfficialInstagramPublishService",),
    ),
    CapabilitySpec(
        name="PerformanceStore",
        tier="current",
        preferred=((".performance_store", "PerformanceStore"),),
    ),
    CapabilitySpec(
        name="decide_mission",
        tier="current",
        preferred=(
            (".mission_control_runtime_bridge", "decide_mission"),
            (".mission_control", "decide_mission"),
        ),
    ),
    CapabilitySpec(
        name="build_creative_plan",
        tier="current",
        preferred=(
            (".creative_planner_runtime_bridge", "build_creative_plan"),
            (".creative_planner", "build_creative_plan"),
        ),
    ),
    CapabilitySpec(
        name="evaluate_editorial_quality",
        tier="current",
        preferred=(
            (".editorial_quality_runtime_bridge", "evaluate_editorial_quality"),
            (".editorial_quality", "evaluate_editorial_quality"),
        ),
    ),
    CapabilitySpec(
        name="build_visual_identity",
        tier="current",
        preferred=(
            (".visual_identity_engine", "build_visual_identity"),
            (".visual_foundation", "build_visual_identity"),
        ),
    ),
    CapabilitySpec(
        name="build_typography_spec",
        tier="current",
        preferred=(
            (".typography_engine", "build_typography_spec"),
            (".visual_foundation", "build_typography_spec"),
        ),
    ),
    CapabilitySpec(
        name="build_visual_contract",
        tier="current",
        preferred=(
            (".visual_contract_engine", "build_visual_contract"),
            (".visual_contract", "build_visual_contract"),
        ),
    ),
    CapabilitySpec(
        name="resolve_visual_template",
        tier="current",
        preferred=(
            (".visual_template_engine", "resolve_visual_template"),
            (".visual_templates", "resolve_visual_template"),
        ),
    ),
    CapabilitySpec(
        name="evaluate_perceptual_quality",
        tier="current",
        preferred=(
            (".perceptual_quality_engine", "evaluate_perceptual_quality"),
            (".perceptual_quality", "evaluate_perceptual_quality"),
        ),
    ),
    CapabilitySpec(
        name="evaluate_visual_quality",
        tier="current",
        preferred=(
            (".visual_quality_engine", "evaluate_visual_quality"),
            (".visual_quality", "evaluate_visual_quality"),
        ),
    ),
    CapabilitySpec(
        name="build_visual_premium_bridge",
        tier="current",
        preferred=((".visual_premium_bridge", "build_visual_premium_bridge"),),
    ),
    CapabilitySpec(
        name="evaluate_rubric_engine",
        tier="current",
        preferred=(
            (".sovereign_gate_bridge", "evaluate_rubric_engine"),
            (".publication_authorization_gate", "evaluate_rubric_engine"),
        ),
    ),
    CapabilitySpec(
        name="evaluate_brand_veto_gate",
        tier="current",
        preferred=(
            (".sovereign_gate_bridge", "evaluate_brand_veto_gate"),
            (".publication_authorization_gate", "evaluate_brand_veto_gate"),
        ),
    ),
    CapabilitySpec(
        name="authorize_publication",
        tier="current",
        preferred=((".publication_authorization_gate", "authorize_publication"),),
    ),
    CapabilitySpec(
        name="resolve_lab_probe_policy",
        tier="current",
        preferred=((".publication_authorization_gate", "resolve_lab_probe_policy"),),
    ),
    CapabilitySpec(
        name="resolve_brand_surface_policy",
        tier="current",
        preferred=((".publication_authorization_gate", "resolve_brand_surface_policy"),),
    ),
    CapabilitySpec(
        name="generate_hook_opening",
        tier="current",
        preferred=(
            (".hook_opening_engine", "generate_hook_opening"),
            (".reel_hook_engine", "generate_hook_opening"),
        ),
    ),
    CapabilitySpec(
        name="ReelStoryboardEngine",
        tier="current",
        preferred=((".reel_storyboard_engine", "ReelStoryboardEngine"),),
    ),
    CapabilitySpec(
        name="ReelRhythmEngine",
        tier="current",
        preferred=((".reel_rhythm_engine", "ReelRhythmEngine"),),
    ),
    CapabilitySpec(
        name="PostProductionPipeline",
        tier="current",
        preferred=((".post_production_pipeline", "PostProductionPipeline"),),
    ),
    CapabilitySpec(
        name="AudioDirectionLayer",
        tier="current",
        preferred=((".audio_direction_layer", "AudioDirectionLayer"),),
    ),
    CapabilitySpec(
        name="MultimodalReelQA",
        tier="current",
        preferred=((".multimodal_reel_qa", "MultimodalReelQA"),),
    ),
    CapabilitySpec(
        name="CinematicGate",
        tier="current",
        preferred=((".cinematic_gate", "CinematicGate"),),
    ),
    CapabilitySpec(
        name="NaturalismEngine",
        tier="current",
        preferred=((".naturalism_engine", "NaturalismEngine"),),
    ),
    CapabilitySpec(
        name="ReleaseAuthority",
        tier="current",
        preferred=((".release_authority", "ReleaseAuthority"),),
    ),
    CapabilitySpec(
        name="PublishGuard",
        tier="current",
        preferred=((".publish_guard", "PublishGuard"),),
    ),
    CapabilitySpec(
        name="build_carousel_sequence",
        tier="current",
        preferred=(
            (".carousel_builder", "build_carousel_sequence"),
            (".carousel_runtime_bridge", "build_carousel_sequence"),
        ),
    ),
    CapabilitySpec(
        name="build_stories_sequence",
        tier="current",
        preferred=(
            (".stories_builder", "build_stories_sequence"),
            (".stories_runtime_bridge", "build_stories_sequence"),
        ),
    ),
    CapabilitySpec(
        name="render_visual_foundation_card",
        tier="current",
        preferred=(
            (".visual_premium_bridge", "render_visual_foundation_card"),
            (".render_visual", "render_visual_foundation_card"),
            (".render_runtime_bridge", "render_visual_foundation_card"),
        ),
    ),
    CapabilitySpec(
        name="DistributionTimingEngine",
        tier="current",
        preferred=(
            (".distribution_timing_engine", "DistributionTimingEngine"),
            (".distribution_timing_engine", "distribution_timing_engine"),
            (".distribution_timing_engine", "build_distribution_timing_engine"),
        ),
    ),
    CapabilitySpec(
        name="ThompsonSampler",
        tier="current",
        preferred=((".thompson_sampler", "ThompsonSampler"),),
    ),
    CapabilitySpec(
        name="RecommendationEngine",
        tier="current",
        preferred=((".recommendation_engine", "RecommendationEngine"),),
    ),
    CapabilitySpec(
        name="resonance_engine",
        tier="current",
        preferred=(
            (".resonance_engine", "resonance_engine"),
            (".resonance_engine", "ResonanceEngine"),
        ),
        aliases=("ResonanceEngine",),
    ),
    CapabilitySpec(
        name="ExperimentRegistry",
        tier="current",
        preferred=((".experiment_registry", "ExperimentRegistry"),),
    ),
    CapabilitySpec(
        name="SerialContinuityEngine",
        tier="future",
        preferred=((".serial_continuity_engine", "build_serial_continuity"),),
        aliases=("build_serial_continuity",),
        notes="registrado oficialmente, mas ainda não é o caminho principal do runtime por resolve_capability",
    ),
    CapabilitySpec(
        name="ReflectionEngine",
        tier="future",
        preferred=((".reflection_engine", "ReflectionEngine"),),
        notes="registrado oficialmente, mas ainda opera prioritariamente por integração direta e adapter",
    ),
    CapabilitySpec(
        name="LLMOrchestrator",
        tier="future",
        preferred=((".llm_orchestrator", "LLMOrchestrator"),),
    ),
    CapabilitySpec(
        name="SeoSocialEngine",
        tier="future",
        preferred=((".seo_social_engine", "SeoSocialEngine"),),
    ),
    CapabilitySpec(
        name="YouTubeAdapter",
        tier="future",
        preferred=((".platform_adapters.youtube", "YouTubeAdapter"),),
    ),
    CapabilitySpec(
        name="TikTokAdapter",
        tier="future",
        preferred=((".platform_adapters.tiktok", "TikTokAdapter"),),
    ),
    CapabilitySpec(
        name="ThreadsAdapter",
        tier="future",
        preferred=((".platform_adapters.threads", "ThreadsAdapter"),),
    ),
)

_SPECS_BY_NAME: dict[str, CapabilitySpec] = {spec.name: spec for spec in _CAPABILITY_SPECS}


def list_capabilities(include_future: bool = True) -> dict[str, list[str]]:
    current = [spec.name for spec in _CAPABILITY_SPECS if spec.tier == "current"]
    future = [spec.name for spec in _CAPABILITY_SPECS if spec.tier == "future"]
    return {
        "current": current,
        "future": future if include_future else [],
    }


@lru_cache(maxsize=None)
def resolve_capability(name: str) -> dict[str, Any]:
    spec = _SPECS_BY_NAME.get(str(name or "").strip())
    if spec is None:
        return {
            "ok": False,
            "name": name,
            "tier": None,
            "symbol": None,
            "module": None,
            "attr": None,
            "error": "capability_not_registered",
        }

    explicit = _try_explicit_paths(spec)
    if explicit and explicit.get("ok"):
        return explicit

    dynamic = _try_dynamic_scan(spec)
    if dynamic.get("ok"):
        return dynamic

    return {
        "ok": False,
        "name": spec.name,
        "tier": spec.tier,
        "symbol": None,
        "module": None,
        "attr": None,
        "error": dynamic.get("error") or (explicit or {}).get("error") or "capability_unresolved",
        "notes": spec.notes,
    }


def capability_registry_snapshot(include_future: bool = True) -> dict[str, Any]:
    current_specs = [spec for spec in _CAPABILITY_SPECS if spec.tier == "current"]
    future_specs = [spec for spec in _CAPABILITY_SPECS if spec.tier == "future"]

    current_names = [spec.name for spec in current_specs]
    future_names = [spec.name for spec in future_specs] if include_future else []

    current_capabilities = [
        {
            "name": spec.name,
            "tier": spec.tier,
            "preferred": [f"{_module_path(module)}:{attr}" for module, attr in spec.preferred],
            "aliases": list(spec.aliases),
            "notes": spec.notes,
        }
        for spec in current_specs
    ]

    future_capabilities = [
        {
            "name": spec.name,
            "tier": spec.tier,
            "preferred": [f"{_module_path(module)}:{attr}" for module, attr in spec.preferred],
            "aliases": list(spec.aliases),
            "notes": spec.notes,
        }
        for spec in future_specs
    ] if include_future else []

    return {
        "ok": True,
        "current_total": len(current_names),
        "future_total": len(future_names),
        "registered_total": len(current_names) + len(future_names),
        "current": current_names,
        "future": future_names,
        "current_capabilities": current_capabilities,
        "future_capabilities": future_capabilities,
    }
