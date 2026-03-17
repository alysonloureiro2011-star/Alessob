from ace.engines.director_engine import build_director_plan
from ace.engines.generator_engine import build_content_package
from ace.engines.media_engine import build_media_package
from ace.engines.publish_engine import publish_content

try:
    from ace.engines.living_myth_engine import myth_run_cycle
except Exception:
    myth_run_cycle = None

try:
    from ace.engines.episodic_memory_engine import register_pipeline_result
except Exception:
    register_pipeline_result = None


PIPELINE_VERSION = "RUN_PIPELINE_LIVING_MYTH_V6_PUBLISH_RECEIPT"


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


def normalize_published_payload(published, media):
    published = dict(published or {})
    publish_result = published.get("publish_result") or {}

    if isinstance(publish_result, dict) and publish_result.get("ok"):
        receipt = {
            "ok": True,
            "publish_status": "published",
            "media_url": publish_result.get("media_url"),
            "container": publish_result.get("container"),
            "published": publish_result.get("published"),
            "published_at": published.get("created_at"),
            "media_path": (media or {}).get("media_path"),
        }
        published["publish_receipt"] = receipt
        published["status"] = "published"
    else:
        receipt = {
            "ok": False,
            "publish_status": "generated",
            "media_path": (media or {}).get("media_path"),
            "published_at": published.get("created_at"),
            "detail": publish_result if isinstance(publish_result, dict) else None,
        }
        published["publish_receipt"] = receipt
        published["status"] = published.get("status") or "generated"

    return published


def run_pipeline(trend=None):
    trend = str(trend or "").strip() or "disciplina com inteligência"

    myth = None
    if myth_run_cycle is not None:
        try:
            myth = myth_run_cycle(trend)
        except Exception:
            myth = None

    myth_line = build_myth_narrative_line(myth)

    plan = build_director_plan(trend)
    content_type = plan["content_type"]
    style = plan["style"]

    content = build_content_package(
        trend=trend,
        style=style,
        content_type=content_type
    )

    content = enrich_content_with_myth(content, myth_line)
    caption = content.get("caption", "")

    media = build_media_package(
        content_type=content_type,
        caption=caption
    )

    published = publish_content(
        trend=trend,
        style=style,
        content_type=content_type,
        caption=caption,
        media_path=media.get("media_path")
    )

    published = normalize_published_payload(published, media)

    plan = dict(plan)
    plan["myth_direction"] = myth.get("narrative_direction") if myth else None
    plan["myth_tension"] = myth.get("dominant_tension") if myth else None
    plan["myth_stage"] = myth.get("chapter_stage") if myth else None

    if isinstance(content, dict):
        content = dict(content)
        content["narrative_direction"] = myth.get("narrative_direction") if myth else None
        content["symbolic_anchor"] = myth.get("symbolic_anchor") if myth else None
        content["cta_mode"] = myth.get("cta_mode") if myth else None
        content["myth_line"] = myth_line

    result = {
        "trend": trend,
        "plan": plan,
        "content": content,
        "media": media,
        "published": published,
        "myth": myth,
        "pipeline_version": PIPELINE_VERSION,
    }

    if register_pipeline_result is not None:
        try:
            register_pipeline_result(result)
        except Exception:
            pass

    return result
