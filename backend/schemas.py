from __future__ import annotations
import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field


# ── LLM output schema (SRS Appendix C) ───────────────────────────────────────

class SocialMediaPost(BaseModel):
    platform: Literal["instagram", "facebook", "tiktok"] = "instagram"
    caption: str = Field(..., min_length=10, max_length=2200)
    hashtags: list[str] = Field(default_factory=list, max_length=30)
    post_time: Optional[datetime.datetime] = None
    image_suggestion: str = ""
    tone: Literal["casual", "professional", "festive", "promotional"] = "casual"


# ── API request/response models ───────────────────────────────────────────────

class GeneratePostRequest(BaseModel):
    tenant_id: str = "hotel_001"
    prompt: str = Field(..., min_length=5, max_length=500)
    platform: Literal["instagram", "facebook", "tiktok"] = "instagram"
    tone: Optional[Literal["casual", "professional", "festive", "promotional"]] = None


class PostResponse(BaseModel):
    id: int
    tenant_id: str
    platform: str
    caption: str
    hashtags: list[str]
    post_time: Optional[datetime.datetime]
    image_suggestion: str
    image_url: Optional[str] = None
    tone: str
    status: str
    prompt: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class PostMetricsResponse(BaseModel):
    post_id: int
    likes: int
    reach: int
    comments: int
    shares: int
    impressions: int
    collected_at: datetime.datetime

    class Config:
        from_attributes = True


class BrandInfoRequest(BaseModel):
    business_name: str
    business_type: str = "boutique_hotel"
    description: str
    target_audience: str
    tone_preference: Literal["casual", "professional", "festive", "promotional"] = "casual"
    location: str = ""


class BrandInfoResponse(BrandInfoRequest):
    tenant_id: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True


class CalendarEntry(BaseModel):
    post_id: int
    platform: str
    caption_preview: str
    scheduled_time: Optional[datetime.datetime]
    status: str


class MonthlyCalendar(BaseModel):
    month: int
    year: int
    entries: list[CalendarEntry]


class KnowledgeBaseItem(BaseModel):
    """
    Tek bir bilgi bankası kalemi.
    text (veya caption) zorunlu; diğerleri opsiyoneldir.
    """
    text: Optional[str] = None       # ana metin — recipe/menu/local_info için
    caption: Optional[str] = None    # brand_voice geriye dönük uyumluluk
    title: Optional[str] = None      # başlık / isim (örn: yemek adı)
    source: Optional[str] = "manual"
    date: Optional[str] = None
    # brand_voice'a özgü
    platform: Optional[str] = None
    hashtags: list[str] = Field(default_factory=list)
    # ek serbest alanlar (fiyat, malzeme vb.)
    extra: dict = Field(default_factory=dict)

    def resolved_text(self) -> str:
        return self.text or self.caption or ""


class IngestRequest(BaseModel):
    tenant_id: str = "hotel_001"
    content_type: Literal[
        "brand_voice", "recipe", "menu", "local_info", "event", "general"
    ] = "brand_voice"
    items: list[KnowledgeBaseItem]

    # Geriye dönük uyumluluk: eski `posts` alanı hâlâ kabul edilir
    posts: Optional[list[dict]] = None

    def resolved_items(self) -> list[dict]:
        if self.items:
            return [i.model_dump() for i in self.items]
        return self.posts or []


class KnowledgeBaseCollectionInfo(BaseModel):
    content_type: str
    label: str
    count: int


class AnalyticsResponse(BaseModel):
    total_posts: int
    approved_posts: int
    rejected_posts: int
    published_posts: int
    approval_rate: float
    avg_likes: float
    avg_reach: float
    avg_comments: float
