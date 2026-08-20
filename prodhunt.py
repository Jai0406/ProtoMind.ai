import os
import re
import html
import time
import logging
import httpx
import feedparser
from dotenv import load_dotenv


load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("ProductHuntEngine")


class ProductHuntGraphQLError(Exception):
    pass

class ProductHuntEngine:
    def __init__(self):
        logger.info("Initializing ProductHuntEngine...")
        self.dev_token = os.getenv("PRODUCTHUNT_DEV_TOKEN")
        self.api_url = "https://api.producthunt.com/v2/api/graphql"
        self.rss_fallback_url = "https://www.producthunt.com/feed"
        
        # Caching Setup (Default TTL: 60 mins = 3600 secs)
        self.cache_ttl = 3600
        self._cache_data = None
        self._cache_engine = None
        self._cache_time = 0
        self.client = None

    async def start(self):
        """Initializes the HTTPX client inside the active event loop."""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=15.0)

    async def fetch_via_api(self):
        """Primary Engine: Fetches top products via GraphQL API."""
        if not self.dev_token:
            raise ValueError("Developer Token missing in .env (set PRODUCTHUNT_DEV_TOKEN).")

        headers = {
            "Authorization": f"Bearer {self.dev_token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

        query = """
        query {
          posts(first: 10, order: RANKING) {
            edges {
              node {
                name
                tagline
                votesCount
                website
                url
                topics(first: 3) {
                  edges {
                    node {
                      name
                    }
                  }
                }
              }
            }
          }
        }
        """

        response = await self.client.post(self.api_url, headers=headers, json={"query": query}, timeout=10)

        if response.status_code != 200:
            response.raise_for_status()

        data = response.json()

        if data.get("errors"):
            error_messages = "; ".join(err.get("message", "Unknown error") for err in data["errors"])
            raise ProductHuntGraphQLError(error_messages)

        posts_payload = data.get("data") or {}
        edges = posts_payload.get("posts", {}).get("edges", [])

        if not edges:
            raise ValueError("API call succeeded but returned zero posts.")

        products = []
        for edge in edges:
            node = edge.get("node", {})
            topics = [t.get("node", {}).get("name") for t in node.get("topics", {}).get("edges", [])]
            category = ", ".join(filter(None, topics)) if topics else "Tech / Software"

            products.append({
                "product_name": node.get("name", "Unknown"),
                "tagline": node.get("tagline", ""),
                "votes": node.get("votesCount", 0),
                "category": category,
                "ph_post_link": node.get("url", ""),
                "direct_website": node.get("website", "")
            })

        return products, "GraphQL API"

    async def fetch_via_rss(self):
        """Emergency Fallback: Fetches from public RSS feed."""
        products = []
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"}
        
        try:
            response = await self.client.get(self.rss_fallback_url, headers=headers, timeout=10)
            response.raise_for_status() # Check for 403 or other HTTP errors
            feed = feedparser.parse(response.content)
        except httpx.RequestError as e:
            print(f"Product Hunt RSS Error: {e}")
            return products, "RSS Fallback Failed"

        if not feed or not hasattr(feed, 'entries'):
            return products, "RSS Fallback Empty"

        for entry in feed.entries[:10]:
            raw_summary = getattr(entry, "summary", "")

            clean_tagline = re.sub(r'<[^<]+?>', '', raw_summary)
            clean_tagline = html.unescape(clean_tagline)
            
            clean_tagline = re.sub(r'\s+Discussion\s*$', '', clean_tagline, flags=re.IGNORECASE).strip()
            clean_tagline = re.sub(r'\s+', ' ', clean_tagline)

            products.append({
                "product_name": entry.title.strip(),
                "tagline": clean_tagline,
                "votes": None,                   
                "category": "Tech / Software",   
                "ph_post_link": entry.link,      
                "direct_website": None           
            })

        return products, "RSS Parser Fallback"

    async def get_top_products(self):
        """
        Controller: Implements caching and automatic fallback from API to RSS.
        """
        current_time = time.time()
        
        if self._cache_data and (current_time - self._cache_time < self.cache_ttl):
            logger.info(f"Serving Product Hunt data from TTL cache (Source: {self._cache_engine}).")
            return self._cache_data, self._cache_engine

        try:
            results, engine_used = await self.fetch_via_api()
            
            self._cache_data = results
            self._cache_engine = engine_used
            self._cache_time = current_time
            
            return results, engine_used
            
        except Exception as e:
            logger.error(f"[CRITICAL ALERT] Primary API Path Failed: {e}. Token may be expired or rate-limited. Switching to Emergency RSS.")
            
            try:
                results, engine_used = await self.fetch_via_rss()
                
                self._cache_data = results
                self._cache_engine = engine_used
                self._cache_time = current_time
                
                return results, engine_used
            except Exception as rss_e:
                logger.error(f"[FATAL] RSS fallback also failed: {rss_e}")
                return [], "Failed"

    async def close(self):
        """Closes the shared HTTPX client gracefully on application shutdown."""
        await self.client.aclose()

if __name__ == "__main__":
    import asyncio

    async def _test():
        engine = ProductHuntEngine()
        print("\n[System] Starting Product Hunt Auto-Fetch Engine...\n")

        top_products, fetch_mode = await engine.get_top_products()

        print("-" * 60)
        print(f"--- TOP TRENDING PRODUCTS (Fetched via: {fetch_mode}) ---")

        for idx, product in enumerate(top_products, 1):
            print(f"[{idx}] Name       : {product['product_name']}")
            print(f"    Tagline    : {product['tagline']}")

            if product['votes'] is not None:
                print(f"    Votes      : {product['votes']}")
            if product['category'] is not None:
                print(f"    Category   : {product['category']}")

            if product['direct_website']:
                print(f"    Direct Web : {product['direct_website']}")

            print(f"    PH Link    : {product['ph_post_link']}")
            print("-" * 60)

        await engine.close()

    asyncio.run(_test())