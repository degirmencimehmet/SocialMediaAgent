"""
Publishing Module — FR-04
Publishes approved posts to Instagram via Meta Graph API.

META GRAPH API KURULUM ADIMLARI:
1. https://developers.facebook.com/apps/ → yeni app oluştur (Business tipi)
2. "Instagram Graph API" ürününü ekle
3. App Review → Instagram: instagram_basic, instagram_content_publish izinlerini iste
4. İşletme Instagram hesabını Facebook Sayfasına bağla
5. System User oluştur ve uzun ömürlü (60 gün) access token al
6. Instagram Business Account ID'yi al: GET /me/accounts → her sayfanın instagram_business_account'unu bul
7. META_ACCESS_TOKEN ve INSTAGRAM_ACCOUNT_ID değerlerini .env'e yaz

NOT: Sandbox/Test modunda yayın sadece hesap sahibine görünür.
Canlıya geçmek için App Review sürecini tamamla.
"""
import logging
import httpx
from datetime import datetime

from config import settings
from database import SessionLocal, Post

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.facebook.com/v19.0"


class PublishingModule:
    def publish(self, post: Post) -> bool:
        """
        Publish an approved post to Instagram.
        Returns True on success, False on failure.
        Sends Telegram notification on success/failure (NFR-USA-03).
        """
        if post.platform != "instagram":
            logger.info("Publishing for %s not yet supported — only Instagram is MVP", post.platform)
            return False

        if not settings.META_ACCESS_TOKEN or not settings.INSTAGRAM_ACCOUNT_ID:
            logger.warning("Meta API credentials not configured")
            return False

        try:
            media_id = self._create_media_container(post)
            self._publish_container(media_id)

            # Update post status in DB
            db = SessionLocal()
            try:
                db_post = db.query(Post).filter(Post.id == post.id).first()
                if db_post:
                    db_post.status = "published"
                    db_post.published_at = datetime.utcnow()
                    db_post.instagram_media_id = media_id
                    db.commit()
            finally:
                db.close()

            self._notify_success(post.id)
            logger.info("Post %d published to Instagram (media_id=%s)", post.id, media_id)
            return True

        except Exception as e:
            logger.error("Publishing failed for post %d: %s", post.id, e)
            self._notify_failure(post.id, str(e))
            return False

    def _create_media_container(self, post: Post) -> str:
        """Step 1: Create a media container (caption-only post, no image URL needed for text)."""
        caption = post.caption + "\n\n" + " ".join(post.hashtags_list())
        url = f"{GRAPH_BASE}/{settings.INSTAGRAM_ACCOUNT_ID}/media"
        params = {
            "caption": caption[:2200],   # Instagram caption limit
            "media_type": "REELS" if False else None,  # extend for video later
            "access_token": settings.META_ACCESS_TOKEN,
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}

        # For caption-only posts (no image) use a placeholder image URL
        # In production the owner would provide an image; here we skip image upload
        params["image_url"] = "https://via.placeholder.com/1080"

        with httpx.Client() as client:
            resp = client.post(url, params=params, timeout=30)
            resp.raise_for_status()
            return resp.json()["id"]

    def _publish_container(self, creation_id: str) -> None:
        """Step 2: Publish the previously created container."""
        url = f"{GRAPH_BASE}/{settings.INSTAGRAM_ACCOUNT_ID}/media_publish"
        params = {
            "creation_id": creation_id,
            "access_token": settings.META_ACCESS_TOKEN,
        }
        with httpx.Client() as client:
            resp = client.post(url, params=params, timeout=30)
            resp.raise_for_status()

    def _notify_success(self, post_id: int):
        try:
            import asyncio
            from modules.telegram_bot import notify_owner
            asyncio.run(notify_owner(
                f"✅ *Gönderi yayınlandı!* (ID: {post_id})\n"
                f"Instagram hesabınızda görüntüleyebilirsiniz."
            ))
        except Exception:
            pass

    def _notify_failure(self, post_id: int, reason: str):
        try:
            import asyncio
            from modules.telegram_bot import notify_owner
            asyncio.run(notify_owner(
                f"⚠️ Gönderi yayınlanamadı (ID: {post_id})\n"
                f"Sebep: _{reason}_\n"
                f"Lütfen içeriği gözden geçirip tekrar deneyin."
            ))
        except Exception:
            pass


publishing_module = PublishingModule()
