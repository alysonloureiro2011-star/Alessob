from pathlib import Path
import time
from PIL import Image, ImageDraw
from moviepy import ImageClip


def build_media_path(base_dir="ace_media", prefix="media", ext=".mp4"):
    Path(base_dir).mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    return str(Path(base_dir) / f"{prefix}_{ts}{ext}")


def generate_image(text, base_dir="ace_media"):
    path = build_media_path(base_dir, "image", ".png")

    img = Image.new("RGB", (1080, 1080), (15, 15, 15))
    draw = ImageDraw.Draw(img)
    draw.text((80, 500), text[:120], fill=(255, 255, 255))

    img.save(path)
    return path


def generate_video(text, base_dir="ace_media"):
    image_path = generate_image(text, base_dir)
    video_path = build_media_path(base_dir, "video", ".mp4")

    clip = ImageClip(image_path, duration=6)

    clip.write_videofile(
        video_path,
        fps=24,
        codec="libx264",
        audio=False
    )

    clip.close()
    return video_path


def build_media_package(content_type, caption):
    if content_type == "reel":
        media_path = generate_video(caption)
    else:
        media_path = generate_image(caption)

    return {
        "content_type": content_type,
        "media_path": media_path,
        "caption": caption
    }
