from pathlib import Path
import time


def build_media_path(base_dir="ace_media", prefix="media", ext=".txt"):
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    return str(Path(base_dir) / f"{prefix}_{ts}{ext}")


def generate_placeholder_image(text, base_dir="ace_media"):
    path = build_media_path(base_dir=base_dir, prefix="image", ext=".txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def generate_placeholder_video(text, base_dir="ace_media"):
    path = build_media_path(base_dir=base_dir, prefix="video", ext=".txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    return path


def build_media_package(content_type, caption):
    if content_type == "reel":
        media_path = generate_placeholder_video(caption)
    else:
        media_path = generate_placeholder_image(caption)

    return {
        "content_type": content_type,
        "media_path": media_path,
        "caption": caption
    }
