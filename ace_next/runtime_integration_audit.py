from __future__ import annotations

"""
ACE Ω — Runtime Integration Audit

Objetivo:
- congelar a lista de módulos que o official_runtime precisa integrar
- permitir auditoria import-safe antes de consolidar o runtime definitivo
- impedir integração cega ou duplicidade silenciosa

Regra:
- este arquivo não executa publish
- este arquivo não altera runtime
- este arquivo só audita presença, importação e contratos mínimos
"""

from dataclasses import asdict, dataclass
import importlib
from typing import Any


@dataclass(frozen=True)
class RuntimeDependency:
    stage: str
    module: str
    symbols: tuple[str, ...]
    critical: bool = True
    purpose: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


RUNTIME_DEPENDENCIES: tuple[RuntimeDependency, ...] = (
    RuntimeDependency(
        stage="config",
        module="ace_next.config",
        symbols=("AceNextConfig", "load_config"),
        purpose="configuração central do runtime oficial",
    ),
    RuntimeDependency(
        stage="mission",
        module="ace_next.mission_control",
        symbols=("decide_mission",),
        purpose="decisão conservadora antes de gerar",
    ),
    RuntimeDependency(
        stage="planner",
        module="ace_next.creative_planner",
        symbols=("build_creative_plan",),
        purpose="planejamento editorial soberano",
    ),
    RuntimeDependency(
        stage="editorial_qa",
        module="ace_next.editorial_rubric",
        symbols=("evaluate_editorial_quality",),
        purpose="gate editorial base",
    ),
    RuntimeDependency(
        stage="visual_contract",
        module="ace_next.visual_contract",
        symbols=("build_visual_contract",),
        purpose="contrato visual do card",
    ),
    RuntimeDependency(
        stage="visual_templates",
        module="ace_next.visual_templates",
        symbols=("resolve_visual_template",),
        purpose="seleção de template visual",
    ),
    RuntimeDependency(
        stage="visual_foundation",
        module="ace_next.visual_foundation_pack",
        symbols=(
            "build_visual_identity",
            "build_typography_spec",
            "evaluate_visual_quality",
            "render_visual_foundation_card",
            "build_carousel_sequence",
            "build_stories_sequence",
        ),
        purpose="núcleo visual premium estático",
    ),
    RuntimeDependency(
        stage="perceptual_qa",
        module="ace_next.perceptual_qa",
        symbols=("evaluate_perceptual_quality",),
        purpose="QA perceptual do visual",
    ),
    RuntimeDependency(
        stage="premium_bridge",
        module="ace_next.visual_premium_bridge",
        symbols=("build_visual_premium_bridge",),
        critical=False,
        purpose="bridge premium de render visual",
    ),
    RuntimeDependency(
        stage="rubric",
        module="ace_next.rubric_engine",
        symbols=("evaluate_rubric_engine",),
        purpose="rubrica soberana quantitativa",
    ),
    RuntimeDependency(
        stage="brand_veto",
        module="ace_next.brand_veto_gate",
        symbols=("evaluate_brand_veto_gate",),
        purpose="proteção de marca",
    ),
    RuntimeDependency(
        stage="authorization",
        module="ace_next.publication_authorization_gate",
        symbols=("authorize_publication",),
        purpose="autorização de publicação por estado",
    ),
    RuntimeDependency(
        stage="reel_stack",
        module="ace_next.hook_opening_engine",
        symbols=("generate_hook_opening",),
        critical=False,
        purpose="abertura forte do reel",
    ),
    RuntimeDependency(
        stage="reel_stack",
        module="ace_next.reel_storyboard_engine",
        symbols=("ReelStoryboardEngine",),
        critical=False,
        purpose="storyboard do reel",
    ),
    RuntimeDependency(
        stage="reel_stack",
        module="ace_next.reel_rhythm_engine",
        symbols=("ReelRhythmEngine",),
        critical=False,
        purpose="ritmo do reel",
    ),
    RuntimeDependency(
        stage="reel_stack",
        module="ace_next.post_production_pipeline",
        symbols=("PostProductionPipeline",),
        critical=False,
        purpose="pós-produção do reel",
    ),
    RuntimeDependency(
        stage="reel_stack",
        module="ace_next.audio_direction_layer",
        symbols=("AudioDirectionLayer",),
        critical=False,
        purpose="direção de áudio",
    ),
    RuntimeDependency(
        stage="reel_stack",
        module="ace_next.multimodal_reel_qa",
        symbols=("MultimodalReelQA",),
        critical=False,
        purpose="QA multimodal do reel",
    ),
    RuntimeDependency(
        stage="reel_stack",
        module="ace_next.cinematic_gate",
        symbols=("CinematicGate",),
        critical=False,
        purpose="gate cinematográfico",
    ),
    RuntimeDependency(
        stage="reel_stack",
        module="ace_next.release_authority",
        symbols=("ReleaseAuthority",),
        critical=False,
        purpose="autoridade de release",
    ),
    RuntimeDependency(
        stage="reel_stack",
        module="ace_next.publish_guard",
        symbols=("PublishGuard",),
        critical=False,
        purpose="guarda final antes do publish",
    ),
    RuntimeDependency(
        stage="publish",
        module="ace_next.publish",
        symbols=("PublishService",),
        purpose="publish truth layer",
    ),
    RuntimeDependency(
        stage="measurement",
        module="ace_next.performance_store",
        symbols=("PerformanceStore",),
        critical=False,
        purpose="armazenamento de performance real",
    ),
)


def _safe_exception(exc: Exception) -> str:
    return f"{type(exc).__name__}: {exc}"


def audit_runtime_dependencies() -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    missing_critical: list[str] = []
    missing_optional: list[str] = []
    broken_modules: list[str] = []

    for dep in RUNTIME_DEPENDENCIES:
        item = dep.to_dict()
        item.update(
            {
                "ok": False,
                "import_ok": False,
                "symbols_ok": False,
                "missing_symbols": [],
                "error": None,
            }
        )

        try:
            mod = importlib.import_module(dep.module)
            item["import_ok"] = True
        except Exception as exc:
            item["error"] = _safe_exception(exc)
            broken_modules.append(dep.module)
            if dep.critical:
                missing_critical.append(dep.module)
            else:
                missing_optional.append(dep.module)
            results.append(item)
            continue

        missing_symbols = [name for name in dep.symbols if not hasattr(mod, name)]
        item["missing_symbols"] = missing_symbols
        item["symbols_ok"] = not missing_symbols
        item["ok"] = item["import_ok"] and item["symbols_ok"]

        if missing_symbols:
            broken_modules.append(dep.module)
            if dep.critical:
                missing_critical.append(dep.module)
            else:
                missing_optional.append(dep.module)
            item["error"] = f"missing_symbols={','.join(missing_symbols)}"

        results.append(item)

    return {
        "ok": not missing_critical,
        "summary": {
            "total_dependencies": len(RUNTIME_DEPENDENCIES),
            "critical_dependencies": sum(1 for dep in RUNTIME_DEPENDENCIES if dep.critical),
            "optional_dependencies": sum(1 for dep in RUNTIME_DEPENDENCIES if not dep.critical),
            "broken_modules": sorted(set(broken_modules)),
            "missing_critical": sorted(set(missing_critical)),
            "missing_optional": sorted(set(missing_optional)),
        },
        "results": results,
    }


def build_runtime_stage_map() -> dict[str, list[dict[str, Any]]]:
    stage_map: dict[str, list[dict[str, Any]]] = {}
    for dep in RUNTIME_DEPENDENCIES:
        stage_map.setdefault(dep.stage, []).append(dep.to_dict())
    return stage_map


def runtime_audit_snapshot() -> dict[str, Any]:
    audit = audit_runtime_dependencies()
    return {
        "ok": audit.get("ok", False),
        "stage_map": build_runtime_stage_map(),
        "summary": audit.get("summary", {}),
    }
