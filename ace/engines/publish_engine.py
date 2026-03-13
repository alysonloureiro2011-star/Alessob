import datetime


def build_publish_record(trend, style, content_type, caption, media_path):
    return {
        "trend": trend,
        "style": style,
        "content_type": content_type,
        "caption": caption,
        "media_path": media_path,
        "published_at": datetime.datetime.utcnow().isoformat(),
        "status": "generated"
    }


def publish_content(trend, style, content_type, caption, media_path):
    return build_publish_record(
        trend=trend,
        style=style,
        content_type=content_type,
        caption=caption,
        media_path=media_path
    )
