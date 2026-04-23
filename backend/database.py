import datetime
import json
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, Text, Boolean, Float
)
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings

engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    platform = Column(String, nullable=False)          # instagram | facebook | tiktok
    caption = Column(Text, nullable=False)
    hashtags = Column(Text, default="[]")              # JSON list
    post_time = Column(DateTime, nullable=True)
    image_suggestion = Column(Text, default="")
    tone = Column(String, default="casual")            # casual | professional | festive | promotional
    status = Column(String, default="pending")         # pending | approved | rejected | published
    prompt = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    telegram_message_id = Column(Integer, nullable=True)
    published_at = Column(DateTime, nullable=True)
    instagram_media_id = Column(String, nullable=True)

    def hashtags_list(self) -> list[str]:
        try:
            return json.loads(self.hashtags or "[]")
        except Exception:
            return []


class PostMetrics(Base):
    __tablename__ = "post_metrics"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, nullable=False, index=True)
    tenant_id = Column(String, nullable=False)
    likes = Column(Integer, default=0)
    reach = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    impressions = Column(Integer, default=0)
    collected_at = Column(DateTime, default=datetime.datetime.utcnow)


class BrandInfo(Base):
    __tablename__ = "brand_info"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, unique=True, nullable=False)
    business_name = Column(String, default="")
    business_type = Column(String, default="boutique_hotel")
    description = Column(Text, default="")
    target_audience = Column(Text, default="")
    tone_preference = Column(String, default="casual")
    location = Column(String, default="")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class IngestionLog(Base):
    __tablename__ = "ingestion_logs"

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(String, nullable=False)
    source = Column(String)          # instagram_api | manual | scrape
    items_ingested = Column(Integer, default=0)
    status = Column(String, default="success")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)
