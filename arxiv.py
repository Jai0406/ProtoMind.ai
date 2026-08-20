import time
import logging
import asyncio
import httpx
import xml.etree.ElementTree as ET

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ArxivEngine")

class ArxivService:
    def __init__(self):
        # FIX: Updated to https to prevent 301 redirects
        self.base_url = "https://export.arxiv.org/api/query"
        
        # Caching dictionaries and TTLs
        self.cache = {}
        self.cache_ttl = 3600         # 1 hour for latest domain papers
        self.search_cache_ttl = 900   # 15 mins for keyword searches
        self.bulk_fetch_size = 50
        
        # FIX: Added follow_redirects=True for robust network handling
        self.client = httpx.AsyncClient(follow_redirects=True)
        self.last_request_time = 0
        self.rate_limit_delay = 3.0   # arXiv recommends 3 seconds delay between requests
        
        # Namespaces for parsing arXiv's Atom XML format
        self.ns = {'atom': 'http://www.w3.org/2005/Atom'}
        
        self.domains = {
            "1": {"name": "Artificial Intelligence", "query": "cat:cs.AI"},
            "2": {"name": "Machine Learning", "query": "cat:cs.LG"},
            "3": {"name": "Computer Vision & Pattern Recognition", "query": "cat:cs.CV"},
            "4": {"name": "Computation and Language (NLP)", "query": "cat:cs.CL"},
            "5": {"name": "Quantitative Finance", "query": "cat:q-fin.*"},
            "6": {"name": "Cryptography and Security", "query": "cat:cs.CR"}
        }

    async def _rate_limit(self):
        """Ensures a minimum delay of 3 seconds between consecutive API calls to respect arXiv guidelines."""
        current_time = time.time()
        time_since_last_call = current_time - self.last_request_time
        
        if time_since_last_call < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last_call
            logger.info(f"Rate limiting active: Sleeping for {sleep_time:.2f} seconds...")
            await asyncio.sleep(sleep_time)
            
        self.last_request_time = time.time()

    def _parse_xml_response(self, xml_data: str) -> list:
        """Parses arXiv XML response and extracts paper details safely."""
        try:
            root = ET.fromstring(xml_data)
            papers = []
            
            for entry in root.findall('atom:entry', self.ns):
                try:
                    # Extract Paper ID (URL)
                    paper_id_url_elem = entry.find('atom:id', self.ns)
                    if paper_id_url_elem is None:
                        continue
                        
                    paper_id_url = paper_id_url_elem.text
                    paper_id = paper_id_url.split('/abs/')[-1]
                    
                    # Extract Title
                    title = entry.find('atom:title', self.ns).text.replace('\n', ' ').strip()
                    
                    # Extract Published Date
                    published = entry.find('atom:published', self.ns).text.split('T')[0]
                    
                    # Extract Authors (First 3 for brevity)
                    authors = [author.find('atom:name', self.ns).text for author in entry.findall('atom:author', self.ns)]
                    authors_str = ", ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
                    
                    # Extract Abstract (Summary)
                    summary = entry.find('atom:summary', self.ns).text.replace('\n', ' ').strip()
                    
                    # Extract Direct PDF Link
                    pdf_link = "Not available"
                    for link in entry.findall('atom:link', self.ns):
                        if link.attrib.get('title') == 'pdf':
                            pdf_link = link.attrib.get('href')
                            # FIX: Convert http to https
                            if pdf_link.startswith("http://"):
                                pdf_link = pdf_link.replace("http://", "https://")
                            break
                    
                    # Fallback to construct PDF link manually if missing from XML
                    if pdf_link == "Not available" and paper_id:
                        pdf_link = f"https://arxiv.org/pdf/{paper_id}" # FIX: Updated to https
                    
                    papers.append({
                        "id": paper_id,
                        "title": title,
                        "date": published,
                        "authors": authors_str,
                        "abstract": summary,
                        "pdf_url": pdf_link,
                        "page_url": paper_id_url.replace("http://", "https://") # FIX: Updated to https
                    })
                except AttributeError as ae:
                    logger.warning(f"Skipping a malformed paper entry due to missing fields: {ae}")
                    continue
                except Exception as e:
                    logger.warning(f"Unexpected error parsing a specific entry: {e}")
                    continue
                
            return papers
        except ET.ParseError as pe:
            logger.error(f"Failed to parse entire XML document: {pe}")
            return []
        except Exception as e:
            logger.error(f"General XML Parsing Error: {e}")
            return []

    async def get_latest_papers(self, category_key: str, max_results: int = 10) -> list:
        if category_key not in self.domains:
            logger.error(f"Invalid category key requested: {category_key}")
            return []
            
        domain = self.domains[category_key]
        cache_key = f"latest_papers_{category_key}"
        now = time.time()
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (now - timestamp) < self.cache_ttl:
                logger.info(f"Serving '{domain['name']}' from TTL cache.")
                return cached_data[:max_results]

        params = {
            "search_query": domain['query'],
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": self.bulk_fetch_size
        }
        
        try:
            await self._rate_limit()
            logger.info(f"Fetching fresh latest papers for '{domain['name']}' from API...")
            resp = await self.client.get(self.base_url, params=params, timeout=15.0)
            resp.raise_for_status()
            
            papers = self._parse_xml_response(resp.text)
            if papers:
                self.cache[cache_key] = (papers, now)
            return papers[:max_results]
        except Exception as e:
            logger.error(f"Error fetching arXiv latest papers: {e}")
            return []

    async def search_papers(self, keyword: str, max_results: int = 10) -> list:
        cache_key = f"search_{keyword}"  # no longer keyed by max_results
        now = time.time()
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if (now - timestamp) < self.search_cache_ttl:
                logger.info(f"Serving search results for '{keyword}' from TTL cache.")
                return cached_data[:max_results]

        params = {
            "search_query": f"all:{keyword}",
            "sortBy": "relevance",
            "sortOrder": "descending",
            "max_results": self.bulk_fetch_size
        }
        
        try:
            await self._rate_limit()
            logger.info(f"Fetching fresh search results for '{keyword}' from API...")
            
            resp = await self.client.get(self.base_url, params=params, timeout=15.0)
            resp.raise_for_status()
            
            papers = self._parse_xml_response(resp.text)
            if papers:
                self.cache[cache_key] = (papers, now)
            return papers[:max_results]
        except Exception as e:
            logger.error(f"Error searching arXiv papers: {e}")
            return []
            
    async def close(self):
        """Closes the shared HTTPX client gracefully on application shutdown."""
        await self.client.aclose()


async def main():
    service = ArxivService()
    print("\n" + "="*60)
    print("SYNAPSE IQ - ARXIV SERVICE TESTER")
    print("="*60)
    
    while True:
        print("\n--- MAIN MENU ---")
        print("1. Discover Latest Research Papers (By Domain)")
        print("2. Search Specific Topic (e.g., 'transformers', 'options pricing')")
        print("3. Exit")
        
        main_choice = input("\nEnter your choice (1/2/3): ").strip()
        
        if main_choice == '3':
            print("\nExiting. Goodbye!\n")
            await service.close()
            break
            
        elif main_choice == '1':
            print("\n--- SELECT A DOMAIN ---")
            for key, val in service.domains.items():
                print(f" [{key}] {val['name']}")
                
            domain_choice = input("\nEnter domain number: ").strip()
            
            print(f"\nFetching Latest Papers...")
            papers = await service.get_latest_papers(domain_choice)
            
            if not papers:
                print("No papers found or invalid choice.")
                continue
                
            print("\n" + "-"*60)
            print(" LATEST RESEARCH PAPERS")
            print("-"*60)
            for idx, p in enumerate(papers):
                print(f"[{idx + 1:2d}] {p['title']}")
                print(f"     Authors: {p['authors']} | Date: {p['date']}")
                print("")
            
            paper_idx = input("Select a paper number to view details (or press Enter to skip): ").strip()
            if not paper_idx: continue
            
            try:
                selected = papers[int(paper_idx) - 1]
                
                print("\n" + "="*60)
                print(" [FOR LLM CONTEXT] - DATA TO BE SENT FOR SUMMARY GENERATION")
                print("="*60)
                print(f"Title:       {selected['title']}")
                print(f"Authors:     {selected['authors']}")
                print(f"Published:   {selected['date']}")
                print(f"Abstract:\n{selected['abstract']}")
                
                print("\n" + "="*60)
                print(" [FOR DASHBOARD/USER] - DIRECT LINKS")
                print("="*60)
                print(f"Direct PDF Download: {selected['pdf_url']}")
                print(f"ArXiv Page Link:     {selected['page_url']}")
                print("="*60 + "\n")
                
            except (ValueError, IndexError):
                print("Invalid selection.")
                
        elif main_choice == '2':
            query = input("\nEnter search keyword/topic: ").strip()
            if not query: continue
            
            print(f"\nSearching arXiv for '{query}'...")
            papers = await service.search_papers(query)
            
            if not papers:
                print("No matches found.")
                continue
                
            print("\n" + "-"*60)
            print(" SEARCH RESULTS (Sorted by Relevance)")
            print("-"*60)
            for idx, p in enumerate(papers):
                print(f"[{idx + 1:2d}] {p['title']}")
                print(f"     Authors: {p['authors']} | Date: {p['date']}")
                print("")
                
            paper_idx = input("Select a paper number to view details (or press Enter to skip): ").strip()
            if not paper_idx: continue
            
            try:
                selected = papers[int(paper_idx) - 1]
                
                print("\n" + "="*60)
                print(" [FOR LLM CONTEXT] - DATA TO BE SENT FOR SUMMARY GENERATION")
                print("="*60)
                print(f"Title:       {selected['title']}")
                print(f"Authors:     {selected['authors']}")
                print(f"Published:   {selected['date']}")
                print(f"Abstract:\n{selected['abstract']}")
                
                print("\n" + "="*60)
                print(" [FOR DASHBOARD/USER] - DIRECT LINKS")
                print("="*60)
                print(f"Direct PDF Download: {selected['pdf_url']}")
                print(f"ArXiv Page Link:     {selected['page_url']}")
                print("="*60 + "\n")        
            except (ValueError, IndexError):
                print("Invalid selection.")

if __name__ == "__main__":
    asyncio.run(main())