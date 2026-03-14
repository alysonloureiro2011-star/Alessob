from pathlib import Path


def validate_media_for_publish(media_path, content_type):
    if not media_path:
        return {"ok": False, "error": "empty_media_path"}

    p = Path(media_path)

    if not p.exists():
        return {"ok": False, "error": "file_not_found"}

    suffix = p.suffix.lower()

    if content_type == "reel" and suffix != ".mp4":
        return {"ok": False, "error": "invalid_video_format"}

    if content_type in ["carrossel", "imagem", "story"] and suffix not in [".png", ".jpg", ".jpeg"]:
        return {"ok": False, "error": "invalid_image_format"}

    return {"ok": True, "media_path": str(p)}
