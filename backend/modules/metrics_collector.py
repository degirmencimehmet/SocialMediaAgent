"""
Performance Analytics Collector — FR-06
Fetches engagement data from Meta Graph API for published posts.
"""
import logging
import httpx
from sqlalchemy.orm import Session

from config import settings
from database import Post, PostMetrics

logger = logging.getLogger(__name__)
GRAPH_BASE = "https://graph.facebook.com/v19.0"


def collect_metrics(post: Post, db: Session) -> None:
    if not post.instagram_media_id or not settings.META_ACCESS_TOKEN:
        return

    try:
        url = f"{GRAPH_BASE}/{post.instagram_media_id}/insights"
        params = {
            "metric": "impressions,reach,likes,comments,shares",
            "access_token": settings.META_ACCESS_TOKEN,
        }
        with httpx.Client() as client:
            resp = client.get(url, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json().get("data", [])

        metrics_map = {item["name"]: item.get("values", [{}])[-1].get("value", 0) for item in data}

        existing = db.query(PostMetrics).filter(PostMetrics.post_id == post.id).first()
        if existing:
            existing.likes = metrics_map.get("likes", 0)
            existing.reach = metrics_map.get("reach", 0)
            existing.comments = metrics_map.get("comments", 0)
            existing.shares = metrics_map.get("shares", 0)
            existing.impressions = metrics_map.get("impressions", 0)
        else:
            db.add(PostMetrics(
                post_id=post.id,
                tenant_id=post.tenant_id,
                likes=metrics_map.get("likes", 0),
                reach=metrics_map.get("reach", 0),
                comments=metrics_map.get("comments", 0),
                shares=metrics_map.get("shares", 0),
                impressions=metrics_map.get("impressions", 0),
            ))
        db.commit()
        logger.info("Metrics collected for post %d", post.id)
    except Exception as e:
        logger.warning("Could not collect metrics for post %d: %s", post.id, e)
