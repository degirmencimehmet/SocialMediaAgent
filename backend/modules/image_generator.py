"""
Image Generator — Gemini Imagen 3 ile görsel üretimi.
Üretilen görseller backend/static/images/ klasörüne kaydedilir.
"""
import logging
import os
import uuid
from pathlib import Path

from google import genai
from google.genai import types

from config import settings

logger = logging.getLogger(__name__)

IMAGES_DIR = Path(__file__).parent.parent / "static" / "images"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_MODEL = "imagen-3.0-generate-002"


def generate_image(image_suggestion: str, caption: str, platform: str = "instagram") -> str | None:
    """
    image_suggestion ve caption'a göre görsel üretir.
    Başarılı olursa kayıt yolunu (/static/images/xxx.png) döner, hata olursa None.
    """
    prompt = _build_prompt(image_suggestion, caption, platform)

    try:
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_images(
            model=IMAGE_MODEL,
            prompt=prompt,
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="1:1",        # Instagram kare format
                safety_filter_level="block_only_high",
                person_generation="allow_adult",
            ),
        )

        if not response.generated_images:
            logger.warning("ImageGenerator: boş yanıt döndü")
            return None

        image_bytes = response.generated_images[0].image.image_bytes
        filename = f"{uuid.uuid4().hex}.png"
        filepath = IMAGES_DIR / filename

        with open(filepath, "wb") as f:
            f.write(image_bytes)

        logger.info("ImageGenerator: görsel kaydedildi → %s", filename)
        return f"/static/images/{filename}"

    except Exception as e:
        logger.error("ImageGenerator: görsel üretilemedi: %s", e)
        return None


def _build_prompt(image_suggestion: str, caption: str, platform: str) -> str:
    base = image_suggestion.strip() if image_suggestion.strip() else "cozy hotel atmosphere"

    style_hints = (
        "Photorealistic, professional photography, warm lighting, "
        "high quality, suitable for social media. "
        "No text, no watermarks, no logos in the image."
    )

    if platform == "instagram":
        style_hints += " Square composition, vibrant colors, Instagram aesthetic."
    elif platform == "tiktok":
        style_hints += " Dynamic, youthful, energetic composition."

    return f"{base}. {style_hints}"
