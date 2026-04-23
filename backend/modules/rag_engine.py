"""
RAG Engine — ChromaDB-backed vector store.
Supports multiple knowledge base types per tenant (NFR-SEC-03: per-tenant isolation).

Koleksiyon adlandırma: {content_type}__{tenant_id}
Örn:
  brand_voice__hotel_001   → geçmiş sosyal medya gönderileri
  recipe__hotel_001        → yemek/içecek tarifleri
  menu__hotel_001          → menü kalemleri ve fiyatları
  local_info__hotel_001    → yerel gezilecek yerler, kültürel bilgiler
  event__hotel_001         → etkinlikler ve duyurular
  general__hotel_001       → diğer her türlü bilgi
"""
import json
import logging
import uuid
from typing import Literal

import chromadb
from chromadb.utils import embedding_functions

from config import settings

logger = logging.getLogger(__name__)

# Desteklenen içerik türleri
ContentType = Literal["brand_voice", "recipe", "menu", "local_info", "event", "general"]

CONTENT_TYPE_LABELS = {
    "brand_voice": "Geçmiş Sosyal Medya Gönderileri",
    "recipe":      "Yemek / İçecek Tarifleri",
    "menu":        "Menü Kalemleri",
    "local_info":  "Yerel Bilgiler / Gezilecek Yerler",
    "event":       "Etkinlikler ve Duyurular",
    "general":     "Genel Bilgi Bankası",
}

# Sorgu sırasında her türden kaç sonuç çekileceği
_DEFAULT_N_PER_TYPE = 4


def _get_embedding_fn():
    if settings.GEMINI_API_KEY:
        return embedding_functions.GoogleGenerativeAiEmbeddingFunction(
            api_key=settings.GEMINI_API_KEY,
            model_name="models/embedding-001",
        )
    return embedding_functions.DefaultEmbeddingFunction()


class RAGEngine:
    def __init__(self):
        self._client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
        self._embedding_fn = _get_embedding_fn()

    # ── Collection helpers ────────────────────────────────────────────────────

    def _col_name(self, content_type: str, tenant_id: str) -> str:
        return f"{content_type}__{tenant_id}"

    def _collection(self, content_type: str, tenant_id: str):
        """Return (or create) a typed, per-tenant ChromaDB collection."""
        return self._client.get_or_create_collection(
            name=self._col_name(content_type, tenant_id),
            embedding_function=self._embedding_fn,
            metadata={"tenant": tenant_id, "content_type": content_type},
        )

    def _existing_collections(self, tenant_id: str) -> list[str]:
        """Return content_type keys that have at least 1 document for this tenant."""
        result = []
        for ctype in CONTENT_TYPE_LABELS:
            try:
                col = self._client.get_collection(
                    name=self._col_name(ctype, tenant_id),
                    embedding_function=self._embedding_fn,
                )
                if col.count() > 0:
                    result.append(ctype)
            except Exception:
                pass
        return result

    # ── Ingest ────────────────────────────────────────────────────────────────

    def ingest(
        self,
        tenant_id: str,
        items: list[dict],
        content_type: ContentType = "brand_voice",
    ) -> int:
        """
        Embed and store knowledge base items.

        Her item dict'i şu alanları destekler:
          - text (str, zorunlu): gömülecek metin
          - title (str, opsiyonel): başlık/etiket
          - source (str, opsiyonel): kaynak (instagram, manual vb.)
          - date (str, opsiyonel)
          - [brand_voice için ek alanlar] platform, hashtags, caption

        Geriye dönük uyumluluk: 'caption' alanı varsa 'text' olarak kullanılır.
        """
        col = self._collection(content_type, tenant_id)
        documents, metadatas, ids = [], [], []

        for i, item in enumerate(items):
            # caption → text (brand_voice geriye dönük uyumluluk)
            text = item.get("text") or item.get("caption", "")
            if not text:
                continue

            doc_id = item.get("id") or f"{tenant_id}__{content_type}__{uuid.uuid4().hex[:8]}_{i}"
            documents.append(text)
            metadatas.append({
                "tenant_id":    tenant_id,
                "content_type": content_type,
                "title":        str(item.get("title", "")),
                "source":       str(item.get("source", "manual")),
                "date":         str(item.get("date", "")),
                # brand_voice specific
                "platform":     str(item.get("platform", "")),
                "hashtags":     json.dumps(item.get("hashtags", [])),
            })
            ids.append(doc_id)

        if documents:
            col.upsert(documents=documents, metadatas=metadatas, ids=ids)
            logger.info(
                "Ingested %d items [%s] for tenant %s",
                len(documents), content_type, tenant_id,
            )

        return len(documents)

    # ── Query ─────────────────────────────────────────────────────────────────

    def query(
        self,
        tenant_id: str,
        query_text: str,
        content_types: list[ContentType] | None = None,
        n_results: int = _DEFAULT_N_PER_TYPE,
    ) -> dict[str, list[str]]:
        """
        Retrieve relevant items from one or more knowledge base collections.

        content_types=None → mevcut tüm koleksiyonları sorgular.
        Döndürülen değer: {content_type: [metin listesi]}
        """
        types_to_query = content_types or self._existing_collections(tenant_id)
        results: dict[str, list[str]] = {}

        for ctype in types_to_query:
            try:
                col = self._client.get_collection(
                    name=self._col_name(ctype, tenant_id),
                    embedding_function=self._embedding_fn,
                )
                count = col.count()
                if count == 0:
                    continue
                res = col.query(
                    query_texts=[query_text],
                    n_results=min(n_results, count),
                )
                docs = res.get("documents", [[]])[0]
                if docs:
                    results[ctype] = docs
            except Exception as e:
                logger.debug("Collection %s query skipped: %s", ctype, e)

        return results

    def query_flat(
        self,
        tenant_id: str,
        query_text: str,
        content_types: list[ContentType] | None = None,
        n_results: int = _DEFAULT_N_PER_TYPE,
    ) -> list[str]:
        """Convenience wrapper — returns a flat list of all retrieved texts."""
        typed = self.query(tenant_id, query_text, content_types, n_results)
        flat = []
        for docs in typed.values():
            flat.extend(docs)
        return flat

    # ── Knowledge base info ───────────────────────────────────────────────────

    def list_collections(self, tenant_id: str) -> list[dict]:
        """Return metadata for all non-empty collections of a tenant."""
        result = []
        for ctype, label in CONTENT_TYPE_LABELS.items():
            try:
                col = self._client.get_collection(
                    name=self._col_name(ctype, tenant_id),
                    embedding_function=self._embedding_fn,
                )
                count = col.count()
                if count > 0:
                    result.append({
                        "content_type": ctype,
                        "label": label,
                        "count": count,
                    })
            except Exception:
                pass
        return result

    def delete_items(self, tenant_id: str, content_type: ContentType, ids: list[str]) -> None:
        """Remove specific items from a collection by ID."""
        col = self._collection(content_type, tenant_id)
        col.delete(ids=ids)
        logger.info("Deleted %d items from [%s] tenant=%s", len(ids), content_type, tenant_id)

    def get_brand_summary(self, tenant_id: str) -> str:
        """Return sample brand_voice posts for tone/style summarization."""
        docs = self.query_flat(tenant_id, "brand tone style writing",
                               content_types=["brand_voice"], n_results=8)
        if not docs:
            return "No historical brand content available."
        return "\n---\n".join(docs[:8])


# Singleton
rag_engine = RAGEngine()
