import os
import time
import logging
import httpx
from datetime import datetime, timedelta
from dotenv import load_dotenv
from config import GITHUB_DOMAINS, CURATED_STANDARDS
from cachetools import TTLCache

load_dotenv()

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("GitHubEngine")


class GitHubService:
    def __init__(self, token=None):
        logger.info("Initializing GitHubService...")
        self.base_url = "https://api.github.com"
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        
        actual_token = token or os.getenv("GITHUB_TOKEN")
        if actual_token:
            self.headers["Authorization"] = f"token {actual_token}"
            logger.info("GitHub Token loaded successfully. Higher rate limits enabled.")
        else:
            logger.warning("No GitHub Token found! API will run in strictly limited unauthenticated mode (60 req/hr).")

        self.trending_cache = TTLCache(maxsize=20, ttl=43200)
        self.general_cache = TTLCache(maxsize=100, ttl=300)
        self.client = None  

    async def start(self):
        """Initializes the HTTPX client inside the active event loop."""
        if self.client is None:
            self.client = httpx.AsyncClient(timeout=15.0)

    def _handle_api_error(self, response: httpx.Response, context: str):
        """FIX 4.4: Centralized error handling to explicitly catch Rate Limits (HTTP 403)."""
        if response.status_code == 403:
            remaining = response.headers.get("X-RateLimit-Remaining", "Unknown")
            reset_time = response.headers.get("X-RateLimit-Reset")
            if reset_time:
                reset_time_str = datetime.fromtimestamp(int(reset_time)).strftime('%H:%M:%S')
            else:
                reset_time_str = "Unknown"
                
            logger.error(f"[CRITICAL] GitHub Rate Limit Hit during '{context}'! Remaining: {remaining}. Resets at: {reset_time_str}.")
        else:
            logger.error(f"HTTP Error {response.status_code} during '{context}': {response.text}")

    async def get_trending_repos(self, category_key: str) -> list:
        if category_key not in GITHUB_DOMAINS:
            logger.error(f"Invalid category key: {category_key}")
            return []
            
        domain = GITHUB_DOMAINS[category_key]
        cache_key = f"trending_{category_key}"
        
        if cache_key in self.trending_cache:
            logger.info(f"Serving trending repos for '{domain['name']}' from cache.")
            return self.trending_cache[cache_key]

        rolling_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        query = f"{domain['query']} created:>{rolling_date}"

        url = f"{self.base_url}/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 15
        }
        
        try:
            logger.info(f"Fetching live trending repos for '{domain['name']}' (Since {rolling_date})...")
            resp = await self.client.get(url, headers=self.headers, params=params, timeout=10)
            
            if resp.status_code != 200:
                self._handle_api_error(resp, "get_trending_repos")
                return []
                
            items = resp.json().get("items", [])
            
            results = []
            for item in items:
                full_name = item.get("full_name")
                results.append({
                    "full_name": full_name,
                    "description": item.get("description") or "No description available.",
                    "stars": item.get("stargazers_count"),
                    "forks": item.get("forks_count", 0),
                    "language": item.get("language") or "Unknown",
                    "html_url": item.get("html_url") or (f"https://github.com/{full_name}" if full_name else None),
                })
                
            if results:
                self.trending_cache[cache_key] = results
            return results
        except httpx.RequestError as e:
            logger.error(f"Network error fetching trending repos: {e}")
            return []

    async def get_curated_details(self, repo_list: list) -> list:
        results = []
        for full_name in repo_list:
            details = await self.get_repo_details(full_name)
            if "error" not in details:
                results.append(details)
        return results
    
    async def search_repositories(self, query: str) -> list:
        cache_key = f"search_{query}"
        
        if cache_key in self.general_cache:
            logger.info(f"Serving search results for '{query}' from cache.")
            return self.general_cache[cache_key]

        url = f"{self.base_url}/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 10
        }
        
        try:
            logger.info(f"Searching GitHub for '{query}'...")
            resp = await self.client.get(url, headers=self.headers, params=params, timeout=10)
            
            if resp.status_code != 200:
                self._handle_api_error(resp, "search_repositories")
                return []
                
            items = resp.json().get("items", [])
            
            results = []
            for item in items:
                full_name = item.get("full_name")
                results.append({
                    "full_name": full_name,
                    "description": item.get("description") or "No description available.",
                    "stars": item.get("stargazers_count"),
                    "forks": item.get("forks_count", 0),
                    "language": item.get("language") or "Unknown",
                    "html_url": item.get("html_url") or (f"https://github.com/{full_name}" if full_name else None),
                })
                
            if results:
                self.general_cache[cache_key] = results
            return results
            
        except httpx.RequestError as e:
            logger.error(f"Network error during search: {e}")
            return []

    async def get_repo_details(self, full_name: str) -> dict:
        cache_key = f"details_{full_name}"
        
        if cache_key in self.general_cache:
            return self.general_cache[cache_key]

        url = f"{self.base_url}/repos/{full_name}"
        try:
            resp = await self.client.get(url, headers=self.headers, timeout=10)
            
            if resp.status_code != 200:
                self._handle_api_error(resp, f"get_repo_details for {full_name}")
                return {"error": f"HTTP {resp.status_code}"}
                
            data = resp.json()
            
            license_data = data.get("license")
            license_name = license_data.get("name") if license_data else "No License Found"
            
            details = {
                "full_name": data.get("full_name"),
                "description": data.get("description") or "No description",
                "stars": data.get("stargazers_count"),
                "forks": data.get("forks_count"),
                "open_issues": data.get("open_issues_count"),
                "language": data.get("language") or "Unknown",
                "html_url": data.get("html_url"),
                "license": license_name,
                "readme_url": f"{data.get('html_url')}#readme"
            }
            
            if "error" not in details:
                self.general_cache[cache_key] = details
            return details
            
        except httpx.RequestError as e:
            logger.error(f"Network error fetching details for '{full_name}': {e}")
            return {"error": str(e)}
        
    async def get_readme_content(self, full_name: str) -> str:
        """Fetches raw README markdown for a specific repo and caches it."""
        cache_key = f"readme_{full_name}"
        
        if cache_key in self.general_cache:
            logger.info(f"Serving README for '{full_name}' from cache.")
            return self.general_cache[cache_key]

        url = f"{self.base_url}/repos/{full_name}/readme"
        
        headers = self.headers.copy()
        headers["Accept"] = "application/vnd.github.v3.raw"
        
        try:
            logger.info(f"Fetching raw README for '{full_name}'...")
            resp = await self.client.get(url, headers=headers, timeout=10)
            
            if resp.status_code != 200:
                self._handle_api_error(resp, f"get_readme_content for {full_name}")
                return "Error: README not found or API rate limit exceeded."
                
            readme_text = resp.text[:3500] 
            
            self.general_cache[cache_key] = readme_text
            return readme_text
            
        except httpx.RequestError as e:
            logger.error(f"Network error fetching README for '{full_name}': {e}")
            return f"Error: Could not fetch README due to network issue."

    async def close(self):
        """Closes the shared HTTPX client gracefully on application shutdown."""
        await self.client.aclose()


if __name__ == "__main__":
    import asyncio

    async def _test():
        service = GitHubService()
        print("\n" + "="*60)
        print("           SYNAPSE IQ - GITHUB SERVICE TESTER")
        print("="*60)
        
        while True:
            print("\n--- MAIN MENU ---")
            print("1. Discover Trending Repositories (By Domain)")
            print("2. Explore Curated Ecosystem Standards (Industry Giants)")
            print("3. Search Specific Repository (For AI Context)")
            print("4. Exit")
            
            main_choice = input("\nEnter your choice (1/2/3/4): ").strip()
            
            if main_choice == '4':
                print("\nExiting. Goodbye!\n")
                await service.close()
                break
                
            elif main_choice == '1':
                print("\n--- SELECT A DOMAIN ---")
                for key, val in GITHUB_DOMAINS.items():
                    print(f" [{key}] {val['name']}")
                    
                domain_choice = input("\nEnter domain number: ").strip()
                
                print(f"\nFetching Top 15 Trending Repos...")
                repos = await service.get_trending_repos(domain_choice)
                
                if not repos:
                    print("No repos found or invalid choice.")
                    continue
                    
                print("\n" + "-"*60)
                print(" TOP TRENDING REPOSITORIES")
                print("-"*60)
                for idx, r in enumerate(repos):
                    print(f"[{idx + 1:2d}] {r['full_name']}")
                    print(f"     Stars: {r['stars']} | Lang: {r['language']}")
                    print(f"     Desc: {r['description'][:100]}...")
                    print("")
                
                repo_idx = input("Select a repo number to view details (or press Enter to skip): ").strip()
                if not repo_idx: continue
                
                try:
                    selected = repos[int(repo_idx) - 1]['full_name']
                    print(f"\nFetching Details for '{selected}'...")
                    details = await service.get_repo_details(selected)
                    
                    print("\n" + "="*60)
                    print(" REPOSITORY DETAILS")
                    print("="*60)
                    print(f"Name:        {details.get('full_name')}")
                    print(f"Description: {details.get('description')}")
                    print(f"License:     {details.get('license')}")
                    print(f"Language:    {details.get('language')}")
                    print(f"Stats:       Stars: {details.get('stars')} | Forks: {details.get('forks')} | Issues: {details.get('open_issues')}")
                    print(f"Repo URL:    {details.get('html_url')}")
                    print(f"README Link: {details.get('readme_url')}")
                    print("="*60 + "\n")
                    
                except (ValueError, IndexError):
                    print("Invalid selection.")

            elif main_choice == '2':
                print("\n--- CURATED ECOSYSTEM STANDARDS ---")
                for key, val in CURATED_STANDARDS.items():
                    print(f" [{key}] {val['category']}")
                    
                curated_choice = input("\nEnter category number: ").strip()
                if curated_choice not in CURATED_STANDARDS:
                    print("Invalid choice.")
                    continue
                    
                category_data = CURATED_STANDARDS[curated_choice]
                
                print("\n" + "-"*60)
                print(f" {category_data['category'].upper()} - INDUSTRY BENCHMARKS")
                print("-"*60)
                
                repos_list = category_data['items']
                for idx, r in enumerate(repos_list):
                    print(f"[{idx + 1:2d}] {r['repo']}")
                    print(f"     Desc: {r['desc']}")
                    print("")
                    
                repo_idx = input("Select a repo number to view deep details (or press Enter to skip): ").strip()
                if not repo_idx: continue
                
                try:
                    selected = repos_list[int(repo_idx) - 1]['repo']
                    print(f"\nFetching Live Stats for '{selected}'...")
                    details = await service.get_repo_details(selected)
                    
                    print("\n" + "="*60)
                    print(" REPOSITORY DETAILS")
                    print("="*60)
                    print(f"Name:        {details.get('full_name')}")
                    print(f"Description: {details.get('description')}")
                    print(f"License:     {details.get('license')}")
                    print(f"Language:    {details.get('language')}")
                    print(f"Stats:       Stars: {details.get('stars')} | Forks: {details.get('forks')} | Issues: {details.get('open_issues')}")
                    print(f"Repo URL:    {details.get('html_url')}")
                    print(f"README Link: {details.get('readme_url')}")
                    print("="*60 + "\n")
                    
                except (ValueError, IndexError):
                    print("Invalid selection.")
                    
            elif main_choice == '3':
                query = input("\nEnter repository name to search: ").strip()
                if not query: continue
                
                print(f"\nSearching GitHub for '{query}'...")
                repos = await service.search_repositories(query)
                if not repos:
                    print("No matches found.")
                    continue
                    
                print("\n" + "-"*60)
                print(" SEARCH RESULTS")
                print("-"*60)
                for idx, r in enumerate(repos):
                    print(f"[{idx + 1:2d}] {r['full_name']}")
                    print(f"     Stars: {r['stars']} | Lang: {r['language']}")
                    print("")
                    
                repo_idx = input("Select a repo number to view details (or press Enter to skip): ").strip()
                if not repo_idx: continue
                
                try:
                    selected = repos[int(repo_idx) - 1]['full_name']
                    print(f"\nFetching Details for '{selected}'...")
                    details = await service.get_repo_details(selected)
                    
                    print("\n" + "="*60)
                    print(" REPOSITORY DETAILS")
                    print("="*60)
                    print(f"Name:        {details.get('full_name')}")
                    print(f"Description: {details.get('description')}")
                    print(f"License:     {details.get('license')}")
                    print(f"Language:    {details.get('language')}")
                    print(f"Stats:       Stars: {details.get('stars')} | Forks: {details.get('forks')} | Issues: {details.get('open_issues')}")
                    print(f"Repo URL:    {details.get('html_url')}")
                    print(f"README Link: {details.get('readme_url')}")
                    print("="*60 + "\n")
                    
                except (ValueError, IndexError):
                    print("Invalid selection.")

    asyncio.run(_test())