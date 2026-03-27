from __future__ import annotations

"""
ACE Ω — Runtime Integration Matrix

Objetivo:
- decidir o que entra AGORA no official_runtime definitivo
- decidir o que entra DEPOIS
- bloquear o que não pode contaminar o núcleo final nesta etapa

Princípio:
- runtime definitivo só integra o que já merece estar no coração do sistema
- módulo parcial só entra com fallback controlado ou fica fora
- nada aleatório entra no núcleo soberano
"""

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RuntimeIntegrationEntry:
    module: str
    symbols: tuple[str, ...]
    status: str
    reason: str
    stage: str
    can_use_fallback: bool = False
    owner_layer: str = "official_runtime"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ENTER_NOW: tuple[RuntimeIntegrationEntry, ...] = (
    RuntimeIntegrationEntry(
        module="ace_next.config",
        symbols=("AceNextConfig", "load_config"),
        status="enter_now",
        reason="configuração central limpa e estável",
        stage="foundation",
    ),
    RuntimeIntegrationEntry(
        module="ace_next.mission_control",
        symbols=("decide_mission",),
        status="enter_now",
        reason="decisão conservadora antes do planner",
        stage="mission",
    ),
    RuntimeIntegrationEntry(
        module="ace_next.creative_planner",
        symbols=("build_creative_plan",),
        status="enter_now",
        reason="planner soberano já maduro o bastante",
        stage="planner",
    ),
    RuntimeIntegrationEntry(
        module="ace_next.editorial_rubric",
        symbols=("evaluate_editorial_quality",),
        status="enter_now",
        reason="QA editorial base confiável",
        stage="editorial_qa",
    ),
    RuntimeIntegrationEntry(
        module="ace_next.visual_contract",
        symbols=("build_visual_contract",),
        status="enter_now",
        reason="contrato visual limpo e determinístico",
        stage="visual_contract",
    ),
    RuntimeIntegrationEntry(
        module="ace_next.visual_templates",
        symbols=("resolve_visual_template",),
        status="enter_now",
        reason="resolvedor de template já utilizável",
        stage="visual_template",
    ),
    RuntimeIntegrationEntry(
        module="ace_next.perceptual_qa",
        symbols=("evaluate_perceptual_quality",),
        status="enter_now",
        reason="QA perceptual já utilizável no núcleo",
        stage="perceptual_qa",
    ),
    RuntimeIntegrationEntry(
        module="ace_next.visual_foundation_pack",
        symbols=(
            "build_visual_identity",
            "build_typography_spec",
            "evaluate_visual_quality",
            "render_visual_foundation_card",
            "build_carousel_sequence",
            "build_stories_sequence",
        ),
        status="enter_now",
        reason="núcleo visual pode entrar com fallback controlado",
        stage="visual_foundation",
        can_use_fallback=True,
    ),
    RuntimeIntegrationEntry(
        module="ace_next.rubric_engine",
        symbols=("evaluate_rubric_engine",),
        status="enter_now",
        reason="rubrica soberana já define pisos quantitativos",
        stage="rubric",
    ),
    RuntimeIntegrationEntry(
        module="ace_next.brand_veto_gate",
        symbols=("evaluate_brand_veto_gate",),
        status="enter_now",
        reason="veto de marca já protege o núcleo",
        stage="brand_veto",
    ),
    RuntimeIntegrationEntry(
        module="ace_next.publication_authorization_gate",
        symbols=("authorize_publication",),
        status="enter_now",
        reason="gate de autorização já determina estado operacional",
        stage="authorization",
    ),
    RuntimeIntegrationEntry(
        module="ace_next.publish_guard",
        symbols=("PublishGuard",),
        status="enter_now",
        reason="guard final leve e objetivo",
        stage="publish_gate",
        can_use_fallback=True,
    ),
    RuntimeIntegrationEntry(
        module="ace_next.publish",
        symbols=("PublishService",),
        status="enter_now",
        reason="publish truth layer já existe e precisa ser costurado ao runtime",
        stage="publish",
    ),
)


ENTER_LATER: tuple[RuntimeIntegrationEntry, ...] = (
    RuntimeIntegrationEntry(
        module="ace_next.performance_store",
        symbols=("PerformanceStore",),
        status="enter_later",
        reason="entra forte depois que measurement real sair do modo slim",
        stage="measurement",
        can_use_fallback=True,
    ),
    RuntimeIntegrationEntry(
        module="ace_next.visual_premium_bridge",
        symbols=("build_visual_premium_bridge",),
        status="enter_later",
        reason="arquitetura aponta para premium headless, mas ambiente ainda não está totalmente consolidado",
        stage="visual_premium",
        can_use_fallback=True,
    ),
    RuntimeIntegrationEntry(
        module="ace_next.reel_storyboard_engine",
        symbols=("ReelStoryboardEngine",),
        status="enter_later",
        reason="entra depois que o contrato do Reel Premium Stack for congelado",
        stage="reel_stack",
        can_use_fallback=True,
    ),
    RuntimeIntegrationEntry(
        module="ace_next.reel_rhythm_engine",
        symbols=("ReelRhythmEngine",),
        status="enter_later",
        reason="entra depois que o stack de reel estiver fechado por contrato",
        stage="reel_stack",
        can_use_fallback=True,
    ),
    RuntimeIntegrationEntry(
        module="ace_next.post_production_pipeline",
        symbols=("PostProductionPipeline",),
        status="enter_later",
        reason="camada ainda mais de decisão do que de execução premium real",
        stage="reel_stack",
        can_use_fallback=True,
    ),
    RuntimeIntegrationEntry(
        module="ace_next.audio_direction_layer",
        symbols=("AudioDirectionLayer",),
        status="enter_later",
        reason="bom como camada, mas não precisa contaminar o runtime final nesta etapa",
        stage="reel_stack",
        can_use_fallback=True,
    ),
    RuntimeIntegrationEntry(
        module="ace_next.multimodal_reel_qa",
        symbols=("MultimodalReelQA",),
        status="enter_later",
        reason="depende de reel stack mais sólido para valer de verdade",
        stage="reel_stack",
        can_use_fallback=True,
    ),
    RuntimeIntegrationEntry(
        module="ace_next.cinematic_gate",
        symbols=("CinematicGate",),
        status="enter_later",
        reason="entra depois da consolidação do stack de reel",
        stage="reel_stack",
        can_use_fallback=True,
    ),
    RuntimeIntegrationEntry(
        module="ace_next.release_authority",
        symbols=("ReleaseAuthority",),
        status="enter_later",
        reason="depende de stack reel e gate cinematográfico maduros",
        stage="reel_stack",
        can_use_fallback=True,
    ),
)


EXCLUDE_FOR_NOW: tuple[RuntimeIntegrationEntry, ...] = (
    RuntimeIntegrationEntry(
        module="ace_next.hook_opening_engine",
        symbols=("generate_hook_opening",),
        status="exclude_for_now",
        reason="usa aleatoriedade e não deve contaminar o núcleo soberano definitivo nesta fase",
        stage="reel_stack",
    ),
)


def build_runtime_integration_matrix() -> dict[str, Any]:
    return {
        "enter_now": [entry.to_dict() for entry in ENTER_NOW],
        "enter_later": [entry.to_dict() for entry in ENTER_LATER],
        "exclude_for_now": [entry.to_dict() for entry in EXCLUDE_FOR_NOW],
    }


def build_final_runtime_contract() -> dict[str, Any]:
    enter_now_modules = [entry.module for entry in ENTER_NOW]
    fallback_modules = [entry.module for entry in ENTER_NOW if entry.can_use_fallback]
    future_modules = [entry.module for entry in ENTER_LATER]
    excluded_modules = [entry.module for entry in EXCLUDE_FOR_NOW]

    return {
        "ok": True,
        "runtime_mode": "definitive_core_without_reel_stack",
        "enter_now_modules": enter_now_modules,
        "fallback_modules": fallback_modules,
        "future_modules": future_modules,
        "excluded_modules": excluded_modules,
        "design_rule": "o runtime definitivo fecha missão, planner, QA, gates, visual base e publish antes do Reel Premium Stack completo",
    }
