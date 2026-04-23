"""
Trend & Competitor Analysis Agent — FR-02
Collects trending hashtags and seasonal keywords via SerpAPI and pytrends.
"""
import logging
from typing import Optional
import requests

from config import settings

logger = logging.getLogger(__name__)

TOURISM_SEED_KEYWORDS = [
    "turkey tourism", "boutique hotel turkey", "turkish hospitality",
    "travel turkey", "holiday turkey", "turquoise coast"
]


class TrendAgent:
    def run(self, location: str = "Turkey", niche: str = "tourism") -> dict:
        """
        Returns:
          - trending_hashtags: list of relevant hashtags
          - trend_summary: human-readable trend context
        """
        hashtags = []
        trend_text = ""

        # 1. Try pytrends (Google Trends) — no API key needed
        try:
            hashtags, trend_text = self._pytrends_fetch(location)
        except Exception as e:
            logger.warning("pytrends failed: %s", e)

        # 2. Try SerpAPI for competitor content if key is configured
        if settings.SERPAPI_KEY:
            try:
                serp_hashtags = self._serpapi_fetch(niche, location)
                hashtags = list(dict.fromkeys(hashtags + serp_hashtags))  # deduplicate
            except Exception as e:
                logger.warning("SerpAPI failed: %s", e)

        # Fallback defaults
        if not hashtags:
            hashtags = self._default_hashtags(niche)
            trend_text = f"Default tourism hashtags for {location}."

        logger.info("TrendAgent: collected %d hashtags", len(hashtags))
        return {
            "trending_hashtags": hashtags[:20],
            "trend_summary": trend_text,
        }

    def _pytrends_fetch(self, location: str) -> tuple[list[str], str]:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="tr-TR", tz=180)
        pt.build_payload(TOURISM_SEED_KEYWORDS[:2], cat=67, timeframe="today 1-m", geo="TR")
        related = pt.related_queries()
        hashtags = []
        for kw in TOURISM_SEED_KEYWORDS[:2]:
            df = related.get(kw, {}).get("top")
            if df is not None and not df.empty:
                for q in df["query"].head(5).tolist():
                    tag = "#" + q.replace(" ", "")
                    hashtags.append(tag)
        trend_text = f"Google Trends (Turkey, last 30 days): {', '.join(hashtags[:5])}"
        return hashtags, trend_text

    def _serpapi_fetch(self, niche: str, location: str) -> list[str]:
        url = "https://serpapi.com/search"
        params = {
            "engine": "google",
            "q": f"{niche} instagram hashtags {location} 2026",
            "api_key": settings.SERPAPI_KEY,
            "num": 5,
        }
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        hashtags = []
        for result in data.get("organic_results", [])[:3]:
            snippet = result.get("snippet", "")
            for word in snippet.split():
                if word.startswith("#") and len(word) > 2:
                    hashtags.append(word)
        return hashtags

    def _default_hashtags(self, niche: str) -> list[str]:
        return [
            "#turkeytravel", "#boutiquhotel", "#turizm", "#turkey",
            "#travel", "#holiday", "#hotel", "#visitturkey",
            "#turkiye", "#tatil", "#otel", "#seyahat",
        ]


trend_agent = TrendAgent()
