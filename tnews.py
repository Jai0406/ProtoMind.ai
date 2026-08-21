import os
import re
import time
import logging
from datetime import datetime, timezone
from urllib.parse import quote
import feedparser
import httpx
import asyncio
from bs4 import BeautifulSoup
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from dotenv import load_dotenv
from config import TECH_SIGNALS, SOURCE_SCORES

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TechNewsEngine")


class TechNewsEngine:
    def __init__(self, cache_ttl=600):
        logger.info("Initializing TechNewsEngine...")
        
        self.analyzer = SentimentIntensityAnalyzer()
        self.cache_ttl = cache_ttl
        self.tech_signals = TECH_SIGNALS
        self.source_scores = SOURCE_SCORES
        self._cache = None
        self._cache_time = 0
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }

    def _clean_html(self, raw_html):
        """Robust HTML stripping using BeautifulSoup."""
        if not raw_html:
            return ""
        soup = BeautifulSoup(raw_html, "html.parser")
        return soup.get_text(separator=" ", strip=True)

    async def _fetch_rss_safe(self, client, url, timeout=10):
        try:
            response = await client.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return feedparser.parse(response.content)
        except Exception as e:
            logger.error(f"Failed to fetch RSS feed from {url}: {e}")
            return None

    async def fetch_google_tech_news(self, client, query="Tech AI DevOps"):
        articles = []
        try:
            time_filtered_query = f"{query} when:15d"
            rss_url = f"https://news.google.com/rss/search?q={quote(time_filtered_query)}&hl=en-US&gl=US&ceid=US:en"
            
            feed = await self._fetch_rss_safe(client, rss_url)
            if not feed:
                return articles

            for entry in feed.entries:
                raw_summary = getattr(entry, "summary", "")
                clean_desc = self._clean_html(raw_summary)
                
                source_name = entry.source.title if hasattr(entry, 'source') and hasattr(entry.source, 'title') else "Google News"
                raw_title = entry.title.strip()
                
                if f" - {source_name}" in raw_title:
                    clean_title = raw_title.rsplit(f" - {source_name}", 1)[0].strip()
                elif " - " in raw_title:
                    clean_title = raw_title.rsplit(" - ", 1)[0].strip()
                else:
                    clean_title = raw_title
                
                articles.append({
                    "title": clean_title,
                    "description": clean_desc,
                    "source": source_name,
                    "publishedAt": entry.published if hasattr(entry, 'published') else "N/A",
                    "url": entry.link,
                    "engine": "google"
                })
        except Exception as e:
            logger.error(f"[Google Fetch Error]: {e}")
        return articles

    async def fetch_tech_crunch(self, client):
        articles = []
        try:
            rss_url = "https://techcrunch.com/feed/"
            feed = await self._fetch_rss_safe(client, rss_url)
            if not feed:
                return articles

            for entry in feed.entries:
                raw_summary = getattr(entry, "summary", "")
                clean_desc = self._clean_html(raw_summary)
                
                articles.append({
                    "title": entry.title.strip(),
                    "description": clean_desc,
                    "source": "TechCrunch",
                    "publishedAt": entry.published if hasattr(entry, 'published') else "N/A",
                    "url": entry.link,
                    "engine": "techcrunch"
                })
        except Exception as e:
            logger.error(f"[TechCrunch Fetch Error]: {e}")
        return articles

    async def fetch_et_tech(self, client):
        articles = []
        try:
            rss_url = "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms"
            feed = await self._fetch_rss_safe(client, rss_url)
            if not feed:
                return articles

            for entry in feed.entries:
                raw_summary = getattr(entry, "summary", "")
                clean_desc = self._clean_html(raw_summary)
                
                articles.append({
                    "title": entry.title.strip(),
                    "description": clean_desc,
                    "source": "Economic Times",
                    "publishedAt": entry.published if hasattr(entry, 'published') else "N/A",
                    "url": entry.link,
                    "engine": "et_tech"
                })
        except Exception as e:
            logger.error(f"[ET Tech Fetch Error]: {e}")
        return articles

    def deduplicate(self, articles):
        seen = set()
        unique_articles = []
        for article in articles:
            clean_key = re.sub(r'\W+', '', article["title"].lower())[:50]
            if clean_key not in seen:
                seen.add(clean_key)
                unique_articles.append(article)
        return unique_articles

    def get_sentiment(self, original_case_text):
        if not original_case_text or not original_case_text.strip():
            return "Neutral"
        # VADER relies heavily on original capitalization, punctuation, and casing
        compound = self.analyzer.polarity_scores(original_case_text)['compound']
        if compound > 0.05:
            return "Positive"
        elif compound < -0.05:
            return "Negative"
        else:
            return "Neutral"

    def _rank_and_score_articles(self, articles):
        ranked_articles = []
        for article in articles:
            title = article['title']
            desc = article['description']
            original_text = f"{title} {desc}"
            sentiment_label = self.get_sentiment(original_text)
            content_lower = original_text.lower()
            
            kw_score = 0
            for category, keywords in self.tech_signals.items():
                for kw in keywords:
                    if re.search(rf'\b{re.escape(kw)}\b', content_lower):
                        kw_score += 1
            
            kw_score_normalized = min(kw_score / 10.0, 1.0)
            
            source_clean = article["source"].lower()
            if source_clean in self.source_scores:
                credibility = self.source_scores[source_clean]
            else:
                credibility = 0.7
                logger.debug(f"Unlisted source detected: '{article['source']}'. Assigned default credibility score: 0.7")
            
            final_score = (kw_score_normalized * 0.6) + (credibility * 0.4)
            
            article["sentiment"] = sentiment_label
            article["score"] = round(final_score, 4)
            ranked_articles.append(article)
            
        ranked_articles.sort(key=lambda x: x["score"], reverse=True)
        return ranked_articles

    async def get_latest_tech_news(self, top_n=None):
        current_time = time.time()

        if self._cache and (current_time - self._cache_time < self.cache_ttl):
            logger.info("Serving tech news from TTL cache.")
            return self._cache[:top_n] if top_n else self._cache

        logger.info("Fetching tech news from all sources concurrently using httpx...")
        all_articles = []

    
        async with httpx.AsyncClient(http2=True) as client:
            google_news, tc_news, et_news = await asyncio.gather(
                self.fetch_google_tech_news(client),
                self.fetch_tech_crunch(client),
                self.fetch_et_tech(client)
            )

        all_articles.extend(google_news)
        all_articles.extend(tc_news)
        all_articles.extend(et_news)

        
        logger.info(f"Total Raw Articles Fetched: {len(all_articles)}")
        
        unique_articles = self.deduplicate(all_articles)
        logger.info(f"Articles after deduplication: {len(unique_articles)}")
        
        ranked_articles = self._rank_and_score_articles(unique_articles)
 
        if ranked_articles:
            self._cache = ranked_articles
            self._cache_time = current_time
        return ranked_articles[:top_n] if top_n else ranked_articles

if __name__ == "__main__":
    async def _test():
        engine = TechNewsEngine()
        print("\n[System] Starting Master Tech News Fetch Test...\n")
        print("-" * 60)

        top_news = await engine.get_latest_tech_news(top_n=None)

        print("\n--- TOP RANKED TECH NEWS ---")
        for idx, article in enumerate(top_news, 1):
            print(f"[{idx}] Title    : {article['title']}")
            print(f"        Source   : {article['source']}")
            print(f"        Date     : {article['publishedAt']}")
            print(f"        Sentiment: {article['sentiment']}")
            print(f"        Score    : {article['score']}")
            print(f"        Link     : {article['url']}")
            print("-" * 60)

    asyncio.run(_test())