"""
Content Generation Agent — FR-01
Uses Google Gemini with structured output (JSON mode) to produce a
validated SocialMediaPost. Implements NFR-PERF-03: ≥95% schema compliance.
"""
import json
import logging
import datetime
import time
from typing import Optional

import google.generativeai as genai

from config import settings
from schemas import SocialMediaPost
from utils.sanitizer import sanitize

logger = logging.getLogger(__name__)

genai.configure(api_key=settings.GEMINI_API_KEY)

SYSTEM_PROMPT = """You are a professional social media content creator specializing in Turkish tourism SMEs.
Your task is to generate engaging, brand-consistent social media posts.

The context you receive may contain multiple knowledge base sections:
- MARKA SESİ / GEÇMİŞ GÖNDERILER → use to match writing style and tone
- YEMEK & İÇECEK TARİFLERİ       → use recipe/ingredient details to make posts mouth-watering
- MENÜ KALEMLERİ                  → use prices, dish names, and descriptions accurately
- YEREL BİLGİLER / GEZİLECEK YERLER → weave in local color and destination highlights
- ETKİNLİKLER & DUYURULAR          → reflect the specific event details
- GENEL BİLGİ BANKASI              → use any other factual business information

Rules:
- Write in the brand's established tone
- If recipe/menu data is present, include accurate details (dish name, key ingredients, price if known)
- Use relevant hashtags (mix Turkish and English)
- Keep captions appropriate for the specified platform
- Instagram captions: up to 2200 characters, emoji-friendly
- Suggest a relevant image that the business owner could take or source
- Do NOT hallucinate facts — only use what appears in the provided context
- Output ONLY valid JSON matching the schema — no extra text

Output schema:
{
  "platform": "instagram" | "facebook" | "tiktok",
  "caption": "<post caption text>",
  "hashtags": ["#tag1", "#tag2", ...],
  "post_time": "<ISO 8601 datetime or null>",
  "image_suggestion": "<description of ideal image>",
  "tone": "casual" | "professional" | "festive" | "promotional"
}"""


class ContentGenerationAgent:
    def __init__(self):
        self._model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.7,
                max_output_tokens=1024,
            ),
            system_instruction=SYSTEM_PROMPT,
        )

    def run(
        self,
        prompt: str,
        platform: str,
        brand_profile: str,
        brand_context: str,
        preferred_tone: str,
        trending_hashtags: list[str],
        trend_summary: str,
    ) -> SocialMediaPost:
        """
        Generates a validated SocialMediaPost.
        Retries once on schema validation failure (NFR-PERF-03).
        """
        clean_prompt = sanitize(prompt)

        user_message = self._build_user_message(
            clean_prompt, platform, brand_profile,
            brand_context, preferred_tone, trending_hashtags, trend_summary
        )

        for attempt in range(3):
            try:
                response = self._model.generate_content(user_message)
                raw = response.text.strip()
                # Remove markdown code fences if present
                if raw.startswith("```"):
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                data = json.loads(raw)
                post = SocialMediaPost(**data)
                logger.info("ContentGenerationAgent: post generated (attempt %d)", attempt + 1)
                return post
            except Exception as e:
                logger.warning("ContentGenerationAgent attempt %d failed: %s", attempt + 1, e)
                if attempt < 2:
                    # 429 rate limit — retry_delay'i parse et, yoksa 15sn bekle
                    wait = 15
                    msg = str(e)
                    if "retry_delay" in msg:
                        import re
                        m = re.search(r'seconds:\s*(\d+)', msg)
                        if m:
                            wait = int(m.group(1)) + 2
                    logger.info("ContentGenerationAgent: %ds bekleniyor...", wait)
                    time.sleep(wait)
                else:
                    raise RuntimeError(f"Content generation failed after 3 attempts: {e}")

    def _build_user_message(
        self, prompt, platform, brand_profile,
        brand_context, preferred_tone, trending_hashtags, trend_summary
    ) -> str:
        now = datetime.datetime.now()
        suggested_time = (now + datetime.timedelta(days=1)).replace(
            hour=18, minute=0, second=0, microsecond=0
        ).isoformat()

        hashtag_str = ", ".join(trending_hashtags[:10]) if trending_hashtags else "none"

        return f"""
OWNER REQUEST: {prompt}

BRAND PROFILE:
{brand_profile}

HISTORICAL BRAND CONTENT (for tone/style reference):
{brand_context or "No historical posts available — use general tourism voice."}

TREND SIGNALS:
{trend_summary}
Trending hashtags to consider: {hashtag_str}

TARGET PLATFORM: {platform}
PREFERRED TONE: {preferred_tone}
SUGGESTED POST TIME (if not specified): {suggested_time}

Generate the post now. Output JSON only.
"""


content_generation_agent = ContentGenerationAgent()
