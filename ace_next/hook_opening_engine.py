"""
ACE Ω — Hook Opening Engine
Responsável pelos primeiros 3 segundos.

Regra soberana aplicada:
- sem aleatoriedade solta no núcleo
- mesma entrada => mesma saída
- variação controlada por contexto
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any


_PATTERN_INTERRUPTS = (
    "zoom rápido",
    "corte seco",
    "mudança de ângulo",
    "efeito glitch leve",
)


def _stable_index(seed: str, size: int, offset: int = 0) -> int:
    digest = sha256(f"{seed}::{offset}".encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % size


def _stable_pick(options: tuple[str, ...], seed: str, offset: int = 0) -> str:
    return options[_stable_index(seed, len(options), offset)]


def _stable_pair(options: tuple[str, ...], seed: str) -> list[str]:
    first_idx = _stable_index(seed, len(options), 11)
    second_idx = _stable_index(seed, len(options), 29)
    if second_idx == first_idx:
        second_idx = (second_idx + 1) % len(options)
    return [options[first_idx], options[second_idx]]


def _intensity_score(seed: str) -> float:
    digest = sha256(f"{seed}::intensity".encode("utf-8")).hexdigest()
    raw = int(digest[:8], 16) / 0xFFFFFFFF
    return round(0.74 + (raw * 0.18), 2)


def generate_hook_opening(trend: str, style: str | None = None, content_type: str | None = None) -> dict[str, Any]:
    trend = str(trend or "tema").strip() or "tema"
    style = str(style or "default").strip().lower() or "default"
    content_type = str(content_type or "image").strip().lower() or "image"
    seed = f"{trend}|{style}|{content_type}"

    visual_hooks = (
        f"movimento brusco + zoom em {trend}",
        f"close extremo com expressão intensa sobre {trend}",
        f"mudança visual inesperada relacionada a {trend}",
        f"contraste forte antes/depois sobre {trend}",
    )

    audio_hooks = (
        f"Você está fazendo isso errado com {trend}",
        f"Ninguém percebe isso sobre {trend}",
        f"Isso muda tudo sobre {trend}",
        f"Se você ignorar isso, vai se arrepender",
    )

    text_hooks = (
        f"o erro invisível sobre {trend}",
        f"por que {trend} não funciona como você pensa",
        f"a verdade que ninguém fala sobre {trend}",
        f"isso explica tudo sobre {trend}",
    )

    if content_type == "reel":
        opening_pattern = "curiosity_gap"
    elif style in {"authority", "authority_shock", "editorial_authority"}:
        opening_pattern = "authority_shock"
    else:
        opening_pattern = "pattern_interrupt"

    return {
        "visual_hook": _stable_pick(visual_hooks, seed, 1),
        "audio_hook": _stable_pick(audio_hooks, seed, 2),
        "text_hook": _stable_pick(text_hooks, seed, 3),
        "pattern_interrupts": _stable_pair(_PATTERN_INTERRUPTS, seed),
        "intensity_score": _intensity_score(seed),
        "opening_pattern": opening_pattern,
        "deterministic": True,
        "seed_key": seed,
    }
