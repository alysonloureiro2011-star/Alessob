from ace.engines.director_engine import build_director_plan
from ace.engines.generator_engine import build_content_package
from ace.engines.media_engine import build_media_package
from ace.engines.publish_engine import publish_content

try:
    from ace.engines.living_myth_engine import myth_run_cycle
except Exception:
    myth_run_cycle = None


PIPELINE_VERSION = "RUN_PIPELINE_LIVING_MYTH_V4_LEGACY_ALIGNED"


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


def enrich_content_with_myth(content, myth_line):
    if not isinstance(content, dict):
        return content

    if not myth_line:
        return content

    content = dict(content)

    base_caption = str(content.get("caption", "")).strip()
    base_text = str(content.get("text", "")).strip()
    base_body = str(content.get("body", "")).strip()

    if base_caption:
        content["caption"] = f"{base_caption}\n\n{myth_line}"
    else:
        content["caption"] = myth_line

    if base_text:
        content["text"] = f"{base_text}\n\n{myth_line}"
    else:
        content["text"] = myth_line

    if base_body:
        content["body"] = f"{base_body}\n\n{myth_line}"
    else:
        content["body"] = myth_line

    return content


def run_pipeline(trend=None):
    """
    Pipeline oficial do ACE Ω alinhado ao caminho legado validado.
    """

    trend = str(trend or "").strip() or "disciplina com inteligência"

    # 1) Myth engine como camada consultiva
    myth = None
    if myth_run_cycle is not None:
        try:
            myth = myth_run_cycle(trend)
        except Exception:
            myth = None

    myth_line = build_myth_narrative_line(myth)

    # 2) Diretor — mesma lógica do legado
    plan = build_director_plan(trend)
    content_type = plan["content_type"]
    style = plan["style"]

    # 3) Gerador — mesma lógica do legado
    content = build_content_package(
        trend=trend,
        style=style,
        content_type=content_type
    )

    # 4) Enriquecimento narrativo leve
    content = enrich_content_with_myth(content, myth_line)

    caption = content.get("caption", "")

    # 5) Mídia — assinatura já validada no legado
    media = build_media_package(
        content_type=content_type,
        caption=caption
    )

    # 6) Publicação — mesma lógica do legado
    published = publish_content(
        trend=trend,
        style=style,
        content_type=content_type,
        caption=caption,
        media_path=media.get("media_path")
    )

    # 7) Expandir plan com myth sem quebrar legado
    plan = dict(plan)
    plan["myth_direction"] = myth.get("narrative_direction") if myth else None
    plan["myth_tension"] = myth.get("dominant_tension") if myth else None
    plan["myth_stage"] = myth.get("chapter_stage") if myth else None

    # 8) Expandir content com myth sem quebrar legado
    if isinstance(content, dict):
        content = dict(content)
        content["narrative_direction"] = myth.get("narrative_direction") if myth else None
        content["symbolic_anchor"] = myth.get("symbolic_anchor") if myth else None
        content["cta_mode"] = myth.get("cta_mode") if myth else None
        content["myth_line"] = myth_line

    return {
        "trend": trend,
        "plan": plan,
        "content": content,
        "media": media,
        "published": published,
        "myth": myth,
        "pipeline_version": PIPELINE_VERSION,
    }
