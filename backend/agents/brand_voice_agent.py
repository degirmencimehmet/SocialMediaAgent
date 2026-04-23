"""
Brand Voice Agent — FR-01 / FR-07
Retrieves content from ALL knowledge base collections (brand_voice, recipe,
menu, local_info, event, general) and builds a structured context string
for the content generation agent.
"""
import logging

from modules.rag_engine import rag_engine, CONTENT_TYPE_LABELS
from database import SessionLocal, BrandInfo

logger = logging.getLogger(__name__)

# Başlıklar Gemini'ye gönderilecek context bölümlerini etiketler
_SECTION_HEADERS = {
    "brand_voice": "MARKA SESİ / GEÇMİŞ GÖNDERILER",
    "recipe":      "YEMEK & İÇECEK TARİFLERİ",
    "menu":        "MENÜ KALEMLERİ",
    "local_info":  "YEREL BİLGİLER / GEZİLECEK YERLER",
    "event":       "ETKİNLİKLER & DUYURULAR",
    "general":     "GENEL BİLGİ BANKASI",
}


class BrandVoiceAgent:
    def run(self, tenant_id: str, prompt: str) -> dict:
        """
        Returns a dict with:
          - brand_context : tüm KB koleksiyonlarından alınan, bölümlendirilmiş metin
          - brand_profile : DB'den gelen yapısal marka bilgisi
          - preferred_tone: marka tercih tonu
          - kb_summary    : hangi koleksiyonlardan kaç belge çekildiğine dair özet
        """
        # 1. Tüm mevcut koleksiyonları sorgula
        typed_results = rag_engine.query(
            tenant_id=tenant_id,
            query_text=prompt,
            content_types=None,   # None → mevcut tüm koleksiyonlar
            n_results=4,
        )

        # 2. Her koleksiyon için başlıklı bölüm oluştur
        sections = []
        kb_summary = []
        for ctype, docs in typed_results.items():
            header = _SECTION_HEADERS.get(ctype, ctype.upper())
            block = f"### {header}\n" + "\n---\n".join(docs)
            sections.append(block)
            kb_summary.append(f"{ctype}: {len(docs)} belge")

        brand_context = "\n\n".join(sections) if sections else ""

        # 3. Marka profilini DB'den çek
        db = SessionLocal()
        try:
            brand = db.query(BrandInfo).filter(BrandInfo.tenant_id == tenant_id).first()
            if brand:
                brand_profile = (
                    f"Business: {brand.business_name}\n"
                    f"Type: {brand.business_type}\n"
                    f"Description: {brand.description}\n"
                    f"Target Audience: {brand.target_audience}\n"
                    f"Preferred Tone: {brand.tone_preference}\n"
                    f"Location: {brand.location}"
                )
                preferred_tone = brand.tone_preference
            else:
                brand_profile = "No brand profile configured yet."
                preferred_tone = "casual"
        finally:
            db.close()

        total_docs = sum(len(d) for d in typed_results.values())
        logger.info(
            "BrandVoiceAgent: %d docs from %d collections for tenant %s",
            total_docs, len(typed_results), tenant_id,
        )

        return {
            "brand_context": brand_context,
            "brand_profile": brand_profile,
            "preferred_tone": preferred_tone,
            "kb_summary": kb_summary,
        }


brand_voice_agent = BrandVoiceAgent()
