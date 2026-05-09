from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


HOOK_OPENING_STUDY_CONTRACT_V1 = {
    "state": "hook_opening_study_contract_v1",
    "first_window_seconds": "0-3",
    "visual_dissonance_zoom_percent": 15,
    "visual_dissonance_interval_ms": 450,
    "micro_expression_duration_ms": 120,
    "micro_expression_frame_window": "15-22",
    "sub_perceptual_audio_hz": 40,
    "sub_perceptual_audio_db": -24,
    "goal": "captura_biologica_inicial",
}

RHYTHM_STUDY_CONTRACT_V1 = {
    "state": "rhythm_study_contract_v1",
    "cadence_pattern": "4-1-2-1",
    "segments": {
        "0_3s": {"cut_ms": 450, "density": "very_high", "goal": "captura_biologica"},
        "3_15s": {"cut_ms": 1200, "density": "medium", "goal": "contexto"},
        "15_45s": {"cut_ms": 850, "density": "high", "goal": "loop_de_tensao"},
        "45_55s": {"cut_ms": 1500, "density": "low", "goal": "climax"},
        "55_60s": {"cut_ms": 300, "density": "very_high", "goal": "micro_hook_replay"},
    },
    "dead_air_policy": "zero_dead_air",
}

NATURALISM_STUDY_CONTRACT_V1 = {
    "state": "naturalism_study_contract_v1",
    "grain_luminance_percent": 2,
    "dynamic_range_profile": "hdr10_plus",
    "pitch_variation_percent_min": 15,
    "pitch_variation_percent_max": 20,
    "foley_db": -40,
    "guardrails": [
        "evitar_perfeicao_plastica",
        "evitar_simetria_artificial_excessiva",
        "preservar_identidade_acima_do_polimento",
        "preservar_legibilidade_acima_do_efeito",
        "parecer_humano_sem_parecer_baguncado",
    ],
}

CINEMATIC_GATE_STUDY_CONTRACT_V1 = {
    "state": "cinematic_gate_study_contract_v1",
    "minimum_cinematic_score": 8.5,
    "requires_vlm_aesthetic_audit": True,
    "requires_rejection_feedback_loop": True,
    "goal": "bloqueio_confiavel_de_peca_mediana",
}

DISTRIBUTION_STUDY_CONTRACT_V1 = {
    "state": "distribution_study_contract_v1",
    "priority_kpis": [
        "share_rate",
        "completion_rate",
        "save_rate",
        "watch_time_ms",
        "replay_rate",
    ],
    "required_blocks": [
        "timing_optimized",
        "dynamic_format_hour_matrix",
        "serial_continuity",
        "seo_social",
    ],
}


@dataclass(frozen=True)
class StudyContractValidation:
    ok: bool
    contract_name: str
    current_state: str
    aligned: bool
    missing: list[str]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _safe_dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _safe_bool(value: Any) -> bool:
    return bool(value)


def validate_rhythm_contract(current_rhythm: dict[str, Any] | None = None) -> dict[str, Any]:
    current_rhythm = _safe_dict(current_rhythm)
    cadence_profile = _safe_dict(current_rhythm.get("cadence_profile"))
    expected = RHYTHM_STUDY_CONTRACT_V1["segments"]

    missing: list[str] = []
    for key, spec in expected.items():
        current_value = cadence_profile.get(key)
        expected_value = f"{spec['cut_ms']}ms"
        if current_value != expected_value:
            missing.append(f"{key}={expected_value}")

    aligned = len(missing) == 0
    return StudyContractValidation(
        ok=True,
        contract_name="rhythm",
        current_state=str(current_rhythm.get("rhythm_state") or "unknown"),
        aligned=aligned,
        missing=missing,
        notes=[
            f"expected_pattern={RHYTHM_STUDY_CONTRACT_V1['cadence_pattern']}",
            f"dead_air_policy={RHYTHM_STUDY_CONTRACT_V1['dead_air_policy']}",
        ],
    ).to_dict()


def validate_naturalism_contract(current_naturalism: dict[str, Any] | None = None) -> dict[str, Any]:
    current_naturalism = _safe_dict(current_naturalism)

    missing: list[str] = []
    if not _safe_bool(current_naturalism.get("apply_micro_variation")):
        missing.append("apply_micro_variation=true")
    if not _safe_bool(current_naturalism.get("apply_texture_hint")):
        missing.append("apply_texture_hint=true")

    aligned = len(missing) == 0
    return StudyContractValidation(
        ok=True,
        contract_name="naturalism",
        current_state=str(current_naturalism.get("naturalism_state") or "unknown"),
        aligned=aligned,
        missing=missing,
        notes=[
            f"grain_luminance_percent={NATURALISM_STUDY_CONTRACT_V1['grain_luminance_percent']}",
            f"dynamic_range_profile={NATURALISM_STUDY_CONTRACT_V1['dynamic_range_profile']}",
            f"pitch_variation_percent={NATURALISM_STUDY_CONTRACT_V1['pitch_variation_percent_min']}-{NATURALISM_STUDY_CONTRACT_V1['pitch_variation_percent_max']}",
            f"foley_db={NATURALISM_STUDY_CONTRACT_V1['foley_db']}",
        ],
    ).to_dict()


def validate_cinematic_gate_contract(current_gate: dict[str, Any] | None = None) -> dict[str, Any]:
    current_gate = _safe_dict(current_gate)
    score = _safe_float(current_gate.get("cinematic_score")) or 0.0

    missing: list[str] = []
    if score < float(CINEMATIC_GATE_STUDY_CONTRACT_V1["minimum_cinematic_score"]):
        missing.append(f"cinematic_score>={CINEMATIC_GATE_STUDY_CONTRACT_V1['minimum_cinematic_score']}")

    aligned = len(missing) == 0
    return StudyContractValidation(
        ok=True,
        contract_name="cinematic_gate",
        current_state=str(current_gate.get("state") or "unknown"),
        aligned=aligned,
        missing=missing,
        notes=[
            f"minimum_cinematic_score={CINEMATIC_GATE_STUDY_CONTRACT_V1['minimum_cinematic_score']}",
            f"requires_vlm_aesthetic_audit={str(CINEMATIC_GATE_STUDY_CONTRACT_V1['requires_vlm_aesthetic_audit']).lower()}",
        ],
    ).to_dict()


def validate_distribution_contract(current_distribution: dict[str, Any] | None = None) -> dict[str, Any]:
    current_distribution = _safe_dict(current_distribution)
    study_tags = _safe_dict(current_distribution.get("study_tags"))

    missing: list[str] = []
    for key in DISTRIBUTION_STUDY_CONTRACT_V1["required_blocks"]:
        if not _safe_bool(study_tags.get(key)):
            missing.append(key)

    aligned = len(missing) == 0
    return StudyContractValidation(
        ok=True,
        contract_name="distribution",
        current_state=str(current_distribution.get("module") or current_distribution.get("state") or "unknown"),
        aligned=aligned,
        missing=missing,
        notes=[
            "priority_kpis=" + ",".join(DISTRIBUTION_STUDY_CONTRACT_V1["priority_kpis"]),
        ],
    ).to_dict()


def build_sovereign_study_contracts_snapshot() -> dict[str, Any]:
    return {
        "ok": True,
        "module": "study_contracts_soberanos_v1",
        "contracts": {
            "hook_opening": HOOK_OPENING_STUDY_CONTRACT_V1,
            "rhythm": RHYTHM_STUDY_CONTRACT_V1,
            "naturalism": NATURALISM_STUDY_CONTRACT_V1,
            "cinematic_gate": CINEMATIC_GATE_STUDY_CONTRACT_V1,
            "distribution": DISTRIBUTION_STUDY_CONTRACT_V1,
        },
        "mode": "declarative_non_runtime",
        "notes": [
            "nao altera comportamento atual",
            "serve como fonte unica dos contratos dos estudos",
            "prepara endurecimento futuro sem tocar no official runtime",
        ],
    }


def study_contracts_examples() -> dict[str, Any]:
    return {
        "snapshot": build_sovereign_study_contracts_snapshot(),
        "rhythm_validation": validate_rhythm_contract(
            {
                "rhythm_state": "phase_4_rhythm_contract_ready",
                "cadence_profile": {
                    "0_3s": "450ms",
                    "3_15s": "1200ms",
                    "15_45s": "850ms",
                    "45_60s": "300ms",
                },
            }
        ),
        "naturalism_validation": validate_naturalism_contract(
            {
                "naturalism_state": "naturalism_engine_ready",
                "apply_micro_variation": True,
                "apply_texture_hint": True,
            }
        ),
        "cinematic_gate_validation": validate_cinematic_gate_contract(
            {
                "state": "phase_4_cinematic_gate_ready",
                "cinematic_score": 8.4,
            }
        ),
        "distribution_validation": validate_distribution_contract(
            {
                "module": "distribution_intelligence_v2",
                "study_tags": {
                    "timing_optimized": True,
                    "dynamic_format_hour_matrix": True,
                    "serial_continuity": True,
                    "seo_social": True,
                },
            }
        ),
    }
