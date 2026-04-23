"""
Scheduler Module — FR-04, NFR-PERF-04
Uses APScheduler to publish posts within ±5 minutes of their scheduled time.
"""
import logging
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from database import SessionLocal, Post

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler(timezone="Europe/Istanbul")


def _publish_post(post_id: int):
    db = SessionLocal()
    try:
        post = db.query(Post).filter(Post.id == post_id).first()
        if not post:
            return
        if post.status != "approved":
            logger.info("Skipping post %d — status is %s", post_id, post.status)
            return
        from modules.publishing import publishing_module
        publishing_module.publish(post)
    finally:
        db.close()


def schedule_post(post: Post) -> None:
    """Queue an approved post for publishing at its scheduled time."""
    if not post.post_time:
        # Publish immediately (within seconds)
        run_at = datetime.utcnow() + timedelta(seconds=10)
    else:
        run_at = post.post_time

    job_id = f"post_{post.id}"
    # Remove existing job if rescheduling
    if _scheduler.get_job(job_id):
        _scheduler.remove_job(job_id)

    _scheduler.add_job(
        _publish_post,
        trigger=DateTrigger(run_date=run_at),
        id=job_id,
        args=[post.id],
        misfire_grace_time=300,   # ±5 minutes tolerance (NFR-PERF-04)
    )
    logger.info("Post %d scheduled for %s", post.id, run_at.isoformat())


def _collect_metrics_job():
    """Periodically fetch engagement metrics for published posts — FR-06."""
    db = SessionLocal()
    try:
        published_posts = db.query(Post).filter(Post.status == "published").all()
        if not published_posts:
            return
        from modules.metrics_collector import collect_metrics
        for post in published_posts:
            collect_metrics(post, db)
    except Exception as e:
        logger.error("Metrics collection failed: %s", e)
    finally:
        db.close()


def start_scheduler():
    """Start the background scheduler and register recurring jobs."""
    if not _scheduler.running:
        # Collect metrics every 6 hours
        _scheduler.add_job(
            _collect_metrics_job,
            trigger=IntervalTrigger(hours=6),
            id="metrics_collector",
            replace_existing=True,
        )
        _scheduler.start()
        logger.info("APScheduler started")


def shutdown_scheduler():
    if _scheduler.running:
        _scheduler.shutdown(wait=False)
