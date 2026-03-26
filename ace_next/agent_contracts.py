from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AgentContract:
    agent_id: str
    input_contract: dict[str, Any]
    output_contract: dict[str, Any]
    validation_rules: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _base_validation_rules() -> list[str]:
    return [
        "saida deve ser dict",
        "sem texto solto fora do contrato",
        "sem campos vazios críticos",
        "sem autorização implícita de brand live",
    ]


def build_agent_contracts() -> dict[str, dict[str, Any]]:
    contracts = [
        AgentContract(
            agent_id="trend_scout",
            input_contract={
                "trend": "str",
                "signal_context": "dict",
                "recent_signal_score": "float|None",
            },
            output_contract={
                "effective_trend": "str",
                "signal_strength": "str",
                "weak_trend": "bool",
                "notes": "list[str]",
            },
            validation_rules=_base_validation_rules(),
        ),
        AgentContract(
            agent_id="editorial_strategist",
            input_contract={
                "effective_trend": "str",
                "brand_context": "dict",
                "recent_memory": "list[dict]",
            },
            output_contract={
                "mission_decision": "dict",
                "planner_overrides": "dict",
                "creative_plan": "dict",
            },
            validation_rules=_base_validation_rules(),
        ),
        AgentContract(
            agent_id="visual_director",
            input_contract={
                "creative_plan": "dict",
                "visual_contract": "dict",
                "brand_context": "dict",
            },
            output_contract={
                "template_choice": "str|None",
                "visual_identity": "dict",
                "visual_risks": "list[str]",
            },
            validation_rules=_base_validation_rules(),
        ),
        AgentContract(
            agent_id="rhythm_editor",
            input_contract={
                "storyboard": "dict",
                "hook_plan": "dict",
                "caption_plan": "dict",
            },
            output_contract={
                "rhythm_plan": "dict",
                "subtitle_plan": "dict",
                "retention_risks": "list[str]",
            },
            validation_rules=_base_validation_rules(),
        ),
        AgentContract(
            agent_id="distribution_strategist",
            input_contract={
                "creative_plan": "dict",
                "performance_memory": "dict",
                "signal_context": "dict",
            },
            output_contract={
                "timing_hypothesis": "str|None",
                "next_format": "str|None",
                "distribution_notes": "list[str]",
            },
            validation_rules=_base_validation_rules(),
        ),
        AgentContract(
            agent_id="reflection_analyst",
            input_contract={
                "real_metrics": "dict",
                "attention_metrics": "dict",
                "recommendation_engine": "dict",
            },
            output_contract={
                "insight": "str",
                "next_hypothesis": "str",
                "reflection_notes": "list[str]",
            },
            validation_rules=_base_validation_rules(),
        ),
    ]
    return {contract.agent_id: contract.to_dict() for contract in contracts}
