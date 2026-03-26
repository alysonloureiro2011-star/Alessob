from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def _safe_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return {}


def _tokens(*parts: Any) -> list[str]:
    out: list[str] = []
    for part in parts:
        text = _clean_text(part).lower()
        for token in text.replace(",", " ").replace(".", " ").split():
            token = token.strip("#.:;!?()[]{}\"'")
            if len(token) >= 4 and token not in out:
                out.append(token)
    return out[:10]


@dataclass(frozen=True)
class HashtagResult:
    ok: bool
    hashtag_state: str
    primary_hashtags: list[str]
    backup_hashtags: list[str]
    notes: list[str]
    guardrails: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class HashtagIntelligence:
    """
    Camada soberana de hashtags.

    Função:
    - gerar hashtags úteis a partir do plano criativo
    - separar hashtags principais e reservas
    - manter coerência com o tema da peça
    """

    def run(
        self,
        *,
        creative_plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        creative_plan = _safe_dict(creative_plan)
        words = _tokens(
            creative_plan.get("headline"),
            creative_plan.get("hook"),
            creative_plan.get("body"),
        )
        primary = [f"#{word}" for word in words[:5]]
        backup = [f"#{word}" for word in words[5:10]]

        result = HashtagResult(
            ok=True,
            hashtag_state="hashtag_intelligence_ready",
            primary_hashtags=primary,
            backup_hashtags=backup,
            notes=[f"hashtags={len(primary) + len(backup)}"],
            guardrails=[
                "hashtags_coerentes_com_o_tema",
                "volume_moderado",
                "clareza_acima_de_excesso",
            ],
        )
        return result.to_dict()


def hashtag_intelligence_examples() -> dict[str, Any]:
    engine = HashtagIntelligence()
    return engine.run(
        creative_plan={
            "headline": "Por que seu conteúdo morre antes de começar",
            "hook": "Seu problema pode estar nos 2 primeiros segundos",
            "body": "Se a abertura não prende, o resto morre junto.",
        }
    )
