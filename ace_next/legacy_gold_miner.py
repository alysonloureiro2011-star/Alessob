from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha1
from typing import Any


HIGH_SIGNAL_TAGS = {
    "premium",
    "official",
    "runtime",
    "sovereign",
    "approved",
    "production",
    "cinematic",
    "naturalism",
    "brand_live",
}

LOW_SIGNAL_TAGS = {
    "draft",
    "test",
    "tmp",
    "deprecated",
    "legacy",
    "old",
    "backup",
    "experiment",
    "prototype",
    "duplicate",
    "fork",
    "patch",
}

CANONICAL_HINTS = {
    "official_runtime",
    "runtime_registry",
    "creative_planner_runtime_bridge",
    "publish_runtime_bridge",
    "rubric_engine",
    "brand_veto_gate",
    "publication_authorization_gate",
}


@dataclass(frozen=True)
class LegacyAssetAssessment:
    asset_id: str
    asset_name: str
    category: str
    score: float
    keep: bool
    canonical_candidate: bool
    duplicate_group: str | None
    risks: list[str]
    strengths: list[str]
    action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LegacyGoldMiner:
    """Triagem aditiva do legado.

    Objetivo: separar o que merece reaproveitamento do que deve ser neutralizado,
    sem tocar no runtime oficial.
    """

    def analyze(self, *, assets: list[dict[str, Any]] | None) -> dict[str, Any]:
        normalized_assets = [_normalize_asset(item) for item in list(assets or []) if isinstance(item, dict)]
        duplicate_map = _duplicate_groups(normalized_assets)

        assessments = [
            self._assess(asset=asset, duplicate_group=duplicate_map.get(asset["asset_id"]))
            for asset in normalized_assets
        ]

        keep_assets = [item for item in assessments if item.keep]
        prune_assets = [item for item in assessments if item.action == "prune"]
        quarantine_assets = [item for item in assessments if item.action == "quarantine"]
        merge_review_assets = [item for item in assessments if item.action == "merge_review"]
        canonical_assets = [item for item in assessments if item.canonical_candidate]

        ranked = sorted(assessments, key=lambda item: (-item.score, item.asset_name.lower()))

        return {
            "ok": True,
            "engine": "LegacyGoldMiner",
            "summary": {
                "total_assets": len(assessments),
                "keep_count": len(keep_assets),
                "prune_count": len(prune_assets),
                "quarantine_count": len(quarantine_assets),
                "merge_review_count": len(merge_review_assets),
                "canonical_candidates": len(canonical_assets),
            },
            "decisions": [item.to_dict() for item in ranked],
            "keep_lane": [item.to_dict() for item in keep_assets],
            "prune_lane": [item.to_dict() for item in prune_assets],
            "quarantine_lane": [item.to_dict() for item in quarantine_assets],
            "merge_review_lane": [item.to_dict() for item in merge_review_assets],
            "canonical_lane": [item.to_dict() for item in canonical_assets],
            "recommendation": _recommendation(
                ranked=ranked,
                canonical_assets=canonical_assets,
                duplicate_map=duplicate_map,
            ),
        }

    def _assess(self, *, asset: dict[str, Any], duplicate_group: str | None) -> LegacyAssetAssessment:
        tags = set(asset.get("tags") or [])
        quality = _clamp(asset.get("quality_score"), default=0.0)
        stability = _clamp(asset.get("stability_score"), default=0.0)
        reuse = _clamp(asset.get("reuse_score"), default=0.0)
        owner_confidence = _clamp(asset.get("owner_confidence"), default=0.0)
        runtime_alignment = _clamp(asset.get("runtime_alignment"), default=0.0)

        score = round(
            (
                quality * 0.28
                + stability * 0.22
                + reuse * 0.18
                + owner_confidence * 0.12
                + runtime_alignment * 0.20
            ),
            2,
        )

        strengths: list[str] = []
        risks: list[str] = []

        if quality >= 8.0:
            strengths.append("qualidade acima do piso premium")
        if stability >= 8.0:
            strengths.append("estabilidade operacional boa")
        if reuse >= 7.8:
            strengths.append("reaproveitamento provável")
        if runtime_alignment >= 8.0:
            strengths.append("alinhado ao núcleo runtime")
        if _is_canonical_candidate(asset=asset, tags=tags):
            strengths.append("sinal forte de canônico")

        if duplicate_group:
            risks.append("possível duplicidade estrutural")
        if _contains_low_signal(tags):
            risks.append("carrega sinais de rascunho ou remendo")
        if runtime_alignment < 6.5:
            risks.append("baixo alinhamento com o núcleo")
        if stability < 6.5:
            risks.append("instabilidade operacional")
        if quality < 6.8:
            risks.append("qualidade insuficiente para trilha premium")

        canonical_candidate = _is_canonical_candidate(asset=asset, tags=tags) and score >= 8.0

        if canonical_candidate and not duplicate_group:
            action = "keep"
            keep = True
        elif duplicate_group and score >= 8.0:
            action = "merge_review"
            keep = True
        elif score >= 7.2 and runtime_alignment >= 7.0:
            action = "keep"
            keep = True
        elif score >= 5.6:
            action = "quarantine"
            keep = False
        else:
            action = "prune"
            keep = False

        return LegacyAssetAssessment(
            asset_id=asset["asset_id"],
            asset_name=asset["asset_name"],
            category=asset["category"],
            score=score,
            keep=keep,
            canonical_candidate=canonical_candidate,
            duplicate_group=duplicate_group,
            risks=risks,
            strengths=strengths,
            action=action,
        )


def analyze_legacy_gold(*, assets: list[dict[str, Any]] | None) -> dict[str, Any]:
    miner = LegacyGoldMiner()
    return miner.analyze(assets=assets)


def legacy_gold_examples() -> dict[str, Any]:
    assets = [
        {
            "asset_id": "1",
            "asset_name": "official_runtime",
            "category": "runtime",
            "quality_score": 8.8,
            "stability_score": 8.2,
            "reuse_score": 9.0,
            "owner_confidence": 9.0,
            "runtime_alignment": 9.5,
            "tags": ["official", "runtime", "production"],
        },
        {
            "asset_id": "2",
            "asset_name": "old_runtime_patch",
            "category": "runtime",
            "quality_score": 5.9,
            "stability_score": 5.4,
            "reuse_score": 5.0,
            "owner_confidence": 4.8,
            "runtime_alignment": 4.9,
            "tags": ["legacy", "patch", "old"],
        },
        {
            "asset_id": "3",
            "asset_name": "publish_runtime_bridge_v1",
            "category": "bridge",
            "quality_score": 8.0,
            "stability_score": 7.9,
            "reuse_score": 8.2,
            "owner_confidence": 7.8,
            "runtime_alignment": 8.4,
            "tags": ["approved", "bridge"],
        },
        {
            "asset_id": "4",
            "asset_name": "publish_runtime_bridge_copy",
            "category": "bridge",
            "quality_score": 7.9,
            "stability_score": 7.5,
            "reuse_score": 8.1,
            "owner_confidence": 7.5,
            "runtime_alignment": 8.1,
            "tags": ["approved", "duplicate"],
        },
    ]
    return analyze_legacy_gold(assets=assets)


def _normalize_asset(asset: dict[str, Any]) -> dict[str, Any]:
    return {
        "asset_id": str(asset.get("asset_id") or _asset_fingerprint(asset)),
        "asset_name": str(asset.get("asset_name") or asset.get("name") or "unknown_asset").strip(),
        "category": str(asset.get("category") or "unknown").strip().lower(),
        "quality_score": asset.get("quality_score"),
        "stability_score": asset.get("stability_score"),
        "reuse_score": asset.get("reuse_score"),
        "owner_confidence": asset.get("owner_confidence"),
        "runtime_alignment": asset.get("runtime_alignment"),
        "tags": _normalize_tags(asset.get("tags")),
    }


def _normalize_tags(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        tag = str(item or "").strip().lower()
        if tag and tag not in normalized:
            normalized.append(tag)
    return normalized


def _duplicate_groups(assets: list[dict[str, Any]]) -> dict[str, str]:
    bucket: dict[str, list[str]] = {}
    for asset in assets:
        fingerprint = _semantic_fingerprint(asset)
        bucket.setdefault(fingerprint, []).append(asset["asset_id"])

    duplicate_map: dict[str, str] = {}
    for fingerprint, asset_ids in bucket.items():
        if len(asset_ids) < 2:
            continue
        for asset_id in asset_ids:
            duplicate_map[asset_id] = fingerprint
    return duplicate_map


def _semantic_fingerprint(asset: dict[str, Any]) -> str:
    base = f"{asset.get('category')}|{asset.get('asset_name', '').lower().replace('_copy', '').replace('_v2', '').replace('_v1', '')}"
    return sha1(base.encode("utf-8")).hexdigest()[:12]


def _asset_fingerprint(asset: dict[str, Any]) -> str:
    base = f"{asset.get('name')}|{asset.get('path')}|{asset.get('category')}"
    return sha1(base.encode("utf-8")).hexdigest()[:12]


def _clamp(value: Any, *, default: float) -> float:
    try:
        numeric = float(value)
    except Exception:
        numeric = default
    return round(min(max(numeric, 0.0), 10.0), 2)


def _contains_low_signal(tags: set[str]) -> bool:
    return any(tag in LOW_SIGNAL_TAGS for tag in tags)


def _is_canonical_candidate(*, asset: dict[str, Any], tags: set[str]) -> bool:
    asset_name = str(asset.get("asset_name") or "").strip().lower()
    return bool(CANONICAL_HINTS.intersection({asset_name})) or any(tag in HIGH_SIGNAL_TAGS for tag in tags)


def _recommendation(
    *,
    ranked: list[LegacyAssetAssessment],
    canonical_assets: list[LegacyAssetAssessment],
    duplicate_map: dict[str, str],
) -> dict[str, Any]:
    top_assets = [item.asset_name for item in ranked[:5]]
    return {
        "top_assets": top_assets,
        "canonical_focus": [item.asset_name for item in canonical_assets[:5]],
        "duplicate_groups": len(set(duplicate_map.values())),
        "next_action": "promover apenas canônicos e revisar duplicados antes de qualquer integração",
    }
