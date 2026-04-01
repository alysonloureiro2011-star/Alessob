from PIL import Image, ImageDraw, ImageFont
import os


def render_visual_premium(payload: dict) -> dict:
    try:
        width, height = 1080, 1350

        img = Image.new("RGB", (width, height), color=(15, 15, 15))
        draw = ImageDraw.Draw(img)

        text = payload.get("body", "Conteúdo ACE")

        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 60)
        except:
            font = ImageFont.load_default()

        draw.text((80, 600), text[:200], fill=(255, 255, 255), font=font)

        output_path = "render_output.jpg"
        img.save(output_path)

        return {
            "ok": True,
            "path": output_path,
            "engine": "pillow",
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "engine": "pillow",
        }
