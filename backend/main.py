"""
FastAPI Application — main entry point.
Starts the Telegram bot in a background thread alongside the API server.
"""
import json
import logging
import threading
import datetime
from contextlib import asynccontextmanager
from typing import Optional

from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session

from config import settings
from database import (
    create_tables, get_db, Post, PostMetrics, BrandInfo, IngestionLog
)
from schemas import (
    GeneratePostRequest, PostResponse, BrandInfoRequest, BrandInfoResponse,
    IngestRequest, AnalyticsResponse, MonthlyCalendar, CalendarEntry,
    KnowledgeBaseCollectionInfo,
)
from agents.orchestrator import orchestrator
from modules.rag_engine import rag_engine
from modules.scheduler import start_scheduler, shutdown_scheduler, schedule_post
from modules.calendar_export import export_json, export_pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    start_scheduler()

    # Start Telegram bot in background thread
    bot_thread = threading.Thread(target=_run_bot, daemon=True)
    bot_thread.start()

    yield
    shutdown_scheduler()


def _run_bot():
    from modules.telegram_bot import run_bot
    run_bot()


app = FastAPI(
    title="AI Social Media Agent",
    description="AI-Powered Social Media Automation for Tourism SMEs",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_static_dir = Path(__file__).parent / "static"
_static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")


# ── Post Generation ───────────────────────────────────────────────────────────

@app.post("/api/generate", response_model=PostResponse, tags=["Posts"])
def generate_post(body: GeneratePostRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Trigger the full pipeline: brand → trends → Gemini → save → Telegram delivery."""
    try:
        post = orchestrator.run(
            db=db,
            tenant_id=body.tenant_id,
            prompt=body.prompt,
            platform=body.platform,
            tone=body.tone,
            send_telegram=True,
        )
        return _post_to_response(post)
    except Exception as e:
        logger.error("Generation error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ── Post Management ───────────────────────────────────────────────────────────

@app.get("/api/posts", response_model=list[PostResponse], tags=["Posts"])
def list_posts(
    tenant_id: str = settings.DEFAULT_TENANT_ID,
    status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    q = db.query(Post).filter(Post.tenant_id == tenant_id)
    if status:
        q = q.filter(Post.status == status)
    posts = q.order_by(Post.created_at.desc()).limit(limit).all()
    return [_post_to_response(p) for p in posts]


@app.get("/api/posts/{post_id}", response_model=PostResponse, tags=["Posts"])
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return _post_to_response(post)


@app.post("/api/posts/{post_id}/approve", response_model=PostResponse, tags=["Posts"])
def approve_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.status = "approved"
    db.commit()
    db.refresh(post)
    schedule_post(post)
    return _post_to_response(post)


@app.post("/api/posts/{post_id}/reject", response_model=PostResponse, tags=["Posts"])
def reject_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post.status = "rejected"
    db.commit()
    db.refresh(post)
    return _post_to_response(post)


# ── Brand Info ────────────────────────────────────────────────────────────────

@app.get("/api/brand", response_model=BrandInfoResponse, tags=["Brand"])
def get_brand(tenant_id: str = settings.DEFAULT_TENANT_ID, db: Session = Depends(get_db)):
    brand = db.query(BrandInfo).filter(BrandInfo.tenant_id == tenant_id).first()
    if not brand:
        raise HTTPException(status_code=404, detail="Brand not configured")
    return brand


@app.put("/api/brand", response_model=BrandInfoResponse, tags=["Brand"])
def upsert_brand(body: BrandInfoRequest, tenant_id: str = settings.DEFAULT_TENANT_ID, db: Session = Depends(get_db)):
    brand = db.query(BrandInfo).filter(BrandInfo.tenant_id == tenant_id).first()
    if brand:
        for k, v in body.model_dump().items():
            setattr(brand, k, v)
    else:
        brand = BrandInfo(tenant_id=tenant_id, **body.model_dump())
        db.add(brand)
    db.commit()
    db.refresh(brand)
    return brand


# ── Brand Content Ingestion (RAG) ─────────────────────────────────────────────

@app.post("/api/ingest", tags=["Knowledge Base"])
def ingest_items(body: IngestRequest, db: Session = Depends(get_db)):
    """
    Bilgi bankasına içerik yükle.
    content_type: brand_voice | recipe | menu | local_info | event | general
    """
    items = body.resolved_items()
    if not items:
        raise HTTPException(status_code=422, detail="En az bir item gerekli (items veya posts).")

    count = rag_engine.ingest(
        tenant_id=body.tenant_id,
        items=items,
        content_type=body.content_type,
    )
    log = IngestionLog(
        tenant_id=body.tenant_id,
        source=body.content_type,
        items_ingested=count,
        status="success",
    )
    db.add(log)
    db.commit()
    return {
        "ingested": count,
        "content_type": body.content_type,
        "tenant_id": body.tenant_id,
    }


@app.get("/api/knowledge-base", response_model=list[KnowledgeBaseCollectionInfo], tags=["Knowledge Base"])
def list_knowledge_base(tenant_id: str = settings.DEFAULT_TENANT_ID):
    """Tenant'ın tüm KB koleksiyonlarını ve döküman sayılarını listele."""
    return rag_engine.list_collections(tenant_id)


@app.delete("/api/knowledge-base/{content_type}", tags=["Knowledge Base"])
def delete_kb_items(
    content_type: str,
    ids: list[str],
    tenant_id: str = settings.DEFAULT_TENANT_ID,
):
    """Belirli ID'lere sahip KB kalemlerini sil."""
    rag_engine.delete_items(tenant_id, content_type, ids)  # type: ignore[arg-type]
    return {"deleted": len(ids), "content_type": content_type}


# ── Analytics ─────────────────────────────────────────────────────────────────

@app.get("/api/analytics", response_model=AnalyticsResponse, tags=["Analytics"])
def get_analytics(tenant_id: str = settings.DEFAULT_TENANT_ID, db: Session = Depends(get_db)):
    posts = db.query(Post).filter(Post.tenant_id == tenant_id).all()
    total = len(posts)
    approved = sum(1 for p in posts if p.status in ("approved", "published"))
    rejected = sum(1 for p in posts if p.status == "rejected")
    published = sum(1 for p in posts if p.status == "published")

    metrics = db.query(PostMetrics).filter(PostMetrics.tenant_id == tenant_id).all()
    avg_likes = sum(m.likes for m in metrics) / len(metrics) if metrics else 0.0
    avg_reach = sum(m.reach for m in metrics) / len(metrics) if metrics else 0.0
    avg_comments = sum(m.comments for m in metrics) / len(metrics) if metrics else 0.0

    return AnalyticsResponse(
        total_posts=total,
        approved_posts=approved,
        rejected_posts=rejected,
        published_posts=published,
        approval_rate=round(approved / total * 100, 1) if total else 0.0,
        avg_likes=round(avg_likes, 1),
        avg_reach=round(avg_reach, 1),
        avg_comments=round(avg_comments, 1),
    )


# ── Calendar ──────────────────────────────────────────────────────────────────

@app.get("/api/calendar", response_model=MonthlyCalendar, tags=["Calendar"])
def get_calendar(
    tenant_id: str = settings.DEFAULT_TENANT_ID,
    year: int = datetime.datetime.now().year,
    month: int = datetime.datetime.now().month,
    db: Session = Depends(get_db),
):
    data = export_json(db, tenant_id, year, month)
    entries = [CalendarEntry(**e) for e in data["entries"]]
    return MonthlyCalendar(month=month, year=year, entries=entries)


@app.get("/api/calendar/pdf", tags=["Calendar"])
def get_calendar_pdf(
    tenant_id: str = settings.DEFAULT_TENANT_ID,
    year: int = datetime.datetime.now().year,
    month: int = datetime.datetime.now().month,
    db: Session = Depends(get_db),
):
    pdf_bytes = export_pdf(db, tenant_id, year, month)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=calendar_{year}_{month:02d}.pdf"},
    )


@app.get("/api/calendar/json", tags=["Calendar"])
def get_calendar_json_file(
    tenant_id: str = settings.DEFAULT_TENANT_ID,
    year: int = datetime.datetime.now().year,
    month: int = datetime.datetime.now().month,
    db: Session = Depends(get_db),
):
    data = export_json(db, tenant_id, year, month)
    return Response(
        content=json.dumps(data, ensure_ascii=False, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=calendar_{year}_{month:02d}.json"},
    )


# ── Trends ────────────────────────────────────────────────────────────────────

@app.get("/api/trends", tags=["Content"])
def get_trends(location: str = "Turkey", niche: str = "tourism"):
    from agents.trend_agent import trend_agent
    return trend_agent.run(location=location, niche=niche)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _post_to_response(post: Post) -> PostResponse:
    image_url = None
    if post.image_path:
        image_url = f"http://localhost:8000{post.image_path}"
    return PostResponse(
        id=post.id,
        tenant_id=post.tenant_id,
        platform=post.platform,
        caption=post.caption,
        hashtags=post.hashtags_list(),
        post_time=post.post_time,
        image_suggestion=post.image_suggestion or "",
        image_url=image_url,
        tone=post.tone,
        status=post.status,
        prompt=post.prompt or "",
        created_at=post.created_at,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
