import os
from pathlib import Path

def safe_video_render(make_video_func, text, trend=None):

    try:
        video = make_video_func(text, trend=trend)

        if video and os.path.exists(video):
            return video

    except Exception as e:
        print("VIDEO FAIL:", e)

    # fallback
    return create_fallback_video(text)


def create_fallback_video(text):

    from PIL import Image, ImageDraw
    from moviepy.editor import ImageClip

    path = Path("ace_media")
    path.mkdir(exist_ok=True)

    img_path = path / "fallback.png"
    video_path = path / "fallback.mp4"

    img = Image.new("RGB",(1080,1920),(10,10,10))
    draw = ImageDraw.Draw(img)

    draw.text((120,900), text[:120], fill=(255,255,255))

    img.save(img_path)

    clip = ImageClip(str(img_path)).set_duration(6)

    clip.write_videofile(
        str(video_path),
        codec="libx264",
        fps=24,
        audio=False
    )

    return str(video_path)
