from ace.engines.trend_engine import choose_trend, normalize_trend
from ace.engines.director_engine import choose_content_type, choose_style
from ace.engines.generator_engine import generate_hook, generate_body
from ace.engines.media_engine import build_media_package
from ace.engines.publish_engine import publish_media

try:
    from ace.engines.living_myth_engine import myth_run_cycle
except Exception:
    myth_run_cycle = None


PIPELINE_VERSION = "RUN_PIPELINE_LIVING_MYTH_V3_MEDIA_FIX"


def build_myth_narrative_line(myth):
    if not myth:
        return None

    stage = myth.get("chapter_stage")
    anchor = myth.get("symbolic_anchor")
    tension = myth.get("dominant_tension")

    if not stage or not anchor or not tension:
        return None

    if stage == "abrir":
        return f"Talvez o verdadeiro eixo aqui seja {anchor}."

    if stage == "aprofundar":
        return f"O conflito real começa quando {anchor} deixa de ser ideia e vira prática."

    return f"No fim, tudo converge para {anchor}."


def run_pipeline(trend=None):
    """
    Pipeline modular oficial do ACE Ω com Living Myth Engine.
    Corrigido para usar a assinatura real de build_media_package.
    """

    result = {}

    # 1) Trend
    if trend is None:
        trend = choose_trend()

    try:
        trend = normalize_trend(trend)
    except Exception:
        pass

    # 2) Living Myth Engine (nunca bloqueante)
    myth = None
    if myth_run_cycle is not None:
        try:
            myth = myth_run_cycle(trend)
        except Exception:
            myth = None

    # 3) Formato e estilo
    content_type = choose_content_type()
    style = choose_style()

    # 4) Geração textual
    hook = generate_hook(trend, style)
    body = generate_body(trend, style)

    # 5) Linha narrativa leve
    myth_line = build_myth_narrative_line(myth)

    if myth_line:
        caption = f"{hook}\n\n{body}\n\n{myth_line}"
    else:
        caption = f"{hook}\n\n{body}"

    # 6) Mídia e publicação
    media = build_media_package(
        content_type=content_type,
        caption=caption
    )
    publish = publish_media(media, caption)

    # 7) Chaves clássicas
    result["trend"] = trend
    result["content_type"] = content_type
    result["style"] = style
    result["caption"] = caption
    result["media"] = media
    result["publish"] = publish

    # 8) Chaves ricas
    result["plan"] = {
        "trend": trend,
        "content_type": content_type,
        "style": style,
        "myth_direction": myth.get("narrative_direction") if myth else None,
        "myth_tension": myth.get("dominant_tension") if myth else None,
        "myth_stage": myth.get("chapter_stage") if myth else None,
    }

    result["content"] = {
        "hook": hook,
        "body": body,
        "caption": caption,
        "narrative_direction": myth.get("narrative_direction") if myth else None,
        "symbolic_anchor": myth.get("symbolic_anchor") if myth else None,
        "cta_mode": myth.get("cta_mode") if myth else None,
        "myth_line": myth_line,
    }

    result["published"] = publish
    result["myth"] = myth
    result["pipeline_version"] = PIPELINE_VERSION

    return result
