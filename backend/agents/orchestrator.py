"""
Orchestrator — FR-01, FR-02, FR-03
Coordinates: BrandVoiceAgent → TrendAgent → ContentGenerationAgent → Telegram delivery.
Acts as the central multi-agent pipeline controller.
"""
import json
import logging
import datetime

from sqlalchemy.orm import Session

from agents.brand_voice_agent import brand_voice_agent
from agents.trend_agent import trend_agent
from agents.content_generation_agent import content_generation_agent
from database import Post, BrandInfo

logger = logging.getLogger(__name__)


class Orchestrator:
    def run(
        self,
        db: Session,
        tenant_id: str,
        prompt: str,
        platform: str = "instagram",
        tone: str | None = None,
        send_telegram: bool = True,
        generate_image: bool = True,
    ) -> Post:
        """
        Full pipeline: brand → trends → generate → save → telegram delivery.
        Returns the saved Post ORM object.
        """
        logger.info("Orchestrator: starting pipeline for tenant=%s prompt='%s'", tenant_id, prompt)

        # ── Step 1: Brand Voice Agent ──────────────────────────────────────────
        brand_data = brand_voice_agent.run(tenant_id, prompt)
        effective_tone = tone or brand_data["preferred_tone"]

        # ── Step 2: Trend Agent ────────────────────────────────────────────────
        brand = db.query(BrandInfo).filter(BrandInfo.tenant_id == tenant_id).first()
        location = brand.location if brand else "Turkey"
        trend_data = trend_agent.run(location=location, niche="tourism")

        # ── Step 3: Content Generation Agent (Gemini) ─────────────────────────
        post_schema = content_generation_agent.run(
            prompt=prompt,
            platform=platform,
            brand_profile=brand_data["brand_profile"],
            brand_context=brand_data["brand_context"],
            preferred_tone=effective_tone,
            trending_hashtags=trend_data["trending_hashtags"],
            trend_summary=trend_data["trend_summary"],
        )

        # ── Step 4: Generate Image (optional) ────────────────────────────────
        image_path = None
        if generate_image:
            try:
                from modules.image_generator import generate_image as _gen_image
                image_path = _gen_image(
                    image_suggestion=post_schema.image_suggestion,
                    caption=post_schema.caption,
                    platform=post_schema.platform,
                )
            except Exception as e:
                logger.error("Orchestrator: image generation failed: %s", e)
        else:
            logger.info("Orchestrator: image generation skipped (text-only mode)")

        # ── Step 5: Persist to DB ─────────────────────────────────────────────
        post = Post(
            tenant_id=tenant_id,
            platform=post_schema.platform,
            caption=post_schema.caption,
            hashtags=json.dumps(post_schema.hashtags),
            post_time=post_schema.post_time,
            image_suggestion=post_schema.image_suggestion,
            image_path=image_path,
            tone=post_schema.tone,
            status="pending",
            prompt=prompt,
        )
        db.add(post)
        db.commit()
        db.refresh(post)

        # ── Step 6: Send to Telegram for approval ────────────────────────────
        if send_telegram:
            try:
                from modules.telegram_bot import send_draft_to_owner
                import asyncio
                asyncio.run(send_draft_to_owner(post))
            except Exception as e:
                logger.error("Orchestrator: Telegram delivery failed: %s", e)
                # Do NOT raise — post is already saved; owner can approve via web UI

        logger.info("Orchestrator: pipeline complete, post_id=%d", post.id)
        return post


orchestrator = Orchestrator()
