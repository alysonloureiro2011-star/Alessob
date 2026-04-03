from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Iterable

_WORD_RE = re.compile(r"[0-9A-Za-zÀ-ÿ_-]+", re.UNICODE)
_SPLIT_RE = re.compile(r"[\n\r\t|]+|(?<=[.!?;:])\s+")

_DEFAULT_BLOCKED = {
    "hook",
    "headline",
    "body",
    "cta",
    "caption",
    "technical_test",
    "internal_lab",
    "brand_live",
    "force_placeholder",
    "force_real_probe",
    "publish_guard",
    "release_authority",
    "runtime",
    "payload",
}

_DEFAULT_STOPWORDS = {
    "a", "as", "o", "os", "e", "de", "da", "do", "das", "dos",
    "para", "por", "com", "sem", "na", "no", "nas", "nos", "em",
    "um", "uma", "uns", "umas",
}


@dataclass(frozen=True)
class TrendInputGuardConfig:
    max_tokens: int = 12
    min_token_len: int = 2
    max_length: int = 180
    blocked_tokens: frozenset[str] = frozenset(_DEFAULT_BLOCKED)
    stopwords: frozenset[str] = frozenset(_DEFAULT_STOPWORDS)


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").strip().split())[:4000]


def _strip_accents(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


def _normalize_token(token: str) -> str:
    return _strip_accents(token).lower().strip("_- ")


def _dedupe_keep_order(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        key = _normalize_token(value)
        if not key or key in seen:
            continue
        seen.add(key)
        ordered.append(value)
    return ordered


def _looks_structural(fragment: str) -> bool:
    punctuation_hits = sum(fragment.count(symbol) for symbol in "{}[]:\"")
    letters = sum(char.isalpha() for char in fragment)
    return punctuation_hits >= 4 and punctuation_hits >= max(2, letters // 2)


def _select_clause(text: str) -> str:
    candidates = [_clean_text(part) for part in _SPLIT_RE.split(text) if _clean_text(part)]
    semantic = [part for part in candidates if not _looks_structural(part)]
    if semantic:
        semantic.sort(key=lambda item: (-len(_WORD_RE.findall(item)), -len(item)))
        return semantic[0]
    return _clean_text(text)


class TrendInputGuard:
    def __init__(self, config: TrendInputGuardConfig | None = None) -> None:
        self.config = config or TrendInputGuardConfig()

    def sanitize(
        self,
        trend: Any,
        *,
        allow_terms: Iterable[str] | None = None,
        deny_terms: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        original_trend = _clean_text(trend)
        selected_clause = _select_clause(original_trend).strip("`'\"")
        selected_clause = _clean_text(selected_clause)[: self.config.max_length]

        allow_set = {_normalize_token(item) for item in (allow_terms or []) if _normalize_token(item)}
        deny_set = {_normalize_token(item) for item in (deny_terms or []) if _normalize_token(item)}

        raw_tokens = _WORD_RE.findall(selected_clause)
        semantic_tokens: list[str] = []
        removed_tokens: list[str] = []
        warnings: list[str] = []

        for token in raw_tokens:
            normalized = _normalize_token(token)
            if not normalized:
                continue
            if normalized in allow_set:
                semantic_tokens.append(token)
                continue
            if normalized in deny_set or normalized in self.config.blocked_tokens:
                removed_tokens.append(token)
                continue
            if len(normalized) < self.config.min_token_len or normalized.isdigit():
                removed_tokens.append(token)
                continue
            if normalized in self.config.stopwords and semantic_tokens:
                continue
            semantic_tokens.append(token)

        semantic_tokens = _dedupe_keep_order(semantic_tokens)[: self.config.max_tokens]
        removed_tokens = _dedupe_keep_order(removed_tokens)
        sanitized_trend = " ".join(semantic_tokens).strip()
        blocked = not bool(sanitized_trend)

        if _looks_structural(original_trend):
            warnings.append("structural_noise_detected")
        if removed_tokens and len(removed_tokens) >= max(2, len(semantic_tokens)):
            warnings.append("high_noise_ratio")
        if len(raw_tokens) > self.config.max_tokens:
            warnings.append("token_budget_applied")

        confidence = 0.92
        if warnings:
            confidence -= min(0.42, 0.08 * len(warnings))
        if blocked:
            confidence = 0.0

        return {
            "ok": not blocked,
            "blocked": blocked,
            "original_trend": original_trend,
            "selected_clause": selected_clause,
            "sanitized_trend": sanitized_trend,
            "changed": sanitized_trend != original_trend,
            "lexical_anchors": semantic_tokens[:8],
            "semantic_tokens": semantic_tokens,
            "removed_tokens": removed_tokens,
            "warnings": warnings,
            "confidence": round(max(0.0, confidence), 2),
            "guard_version": "trend_input_guard_v1",
        }


_DEFAULT_GUARD = TrendInputGuard()


def sanitize_trend_input(
    trend: Any,
    *,
    allow_terms: Iterable[str] | None = None,
    deny_terms: Iterable[str] | None = None,
) -> dict[str, Any]:
    return _DEFAULT_GUARD.sanitize(trend, allow_terms=allow_terms, deny_terms=deny_terms)
