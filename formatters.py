import urllib.parse
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

# ==========================================
# PYDANTIC DATA MODELS (For FastAPI & Solara)
# ==========================================

class BasePaginatedResponse(BaseModel):
    has_more: bool
    next_offset: Optional[int]
    total_returned: int

class NewsItem(BaseModel):
    id: int
    title: str
    description: str  # FIX: Added missing description field
    url: str
    date: str
    source: str = "Unknown"
    sentiment: str = "Neutral"

class PaginatedNews(BasePaginatedResponse):
    items: List[NewsItem]

class ProductItem(BaseModel):
    id: int
    name: str
    tagline: str
    votes: int
    category: str
    ph_link: str
    direct_link: Optional[str]

class PaginatedProducts(BasePaginatedResponse):
    items: List[ProductItem]

class RepoItem(BaseModel):
    id: int
    name: str
    description: str
    stars: int
    forks: int
    language: str
    html_url: str

class PaginatedRepos(BasePaginatedResponse):
    items: List[RepoItem]

class PaperItem(BaseModel):
    id: int
    title: str
    authors: str
    date: str
    page_url: str
    pdf_url: str
    abstract: str

class PaginatedPapers(BasePaginatedResponse):
    items: List[PaperItem]

class SummaryResult(BaseModel):
    content: str
    read_more_url: Optional[str] = None
    is_fallback: bool = False
    header_label: Optional[str] = None

# UTILITY FUNCTIONS

def clean_ph_link(url: str) -> str:
    """Strips UTM tracking parameters from URLs to clean up outgoing links."""
    if not url:
        return ""
    parsed = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed.query)
    cleaned_params = {k: v for k, v in query_params.items() if not k.startswith('utm_')}
    parsed = parsed._replace(query=urllib.parse.urlencode(cleaned_params, doseq=True))
    return urllib.parse.urlunparse(parsed)

# DATA FORMATTERS
def format_news_list(articles: List[Dict[str, Any]], offset: int = 0, limit: int = 5) -> PaginatedNews:
    """Formats tech news list into structured Pydantic models."""
    sliced = articles[offset : offset + limit]
    items = []
    
    for i, article in enumerate(sliced):
        items.append(NewsItem(
            id=offset + i,
            title=article.get('title', 'Unknown Title'),
            description=article.get('description', 'No description available.'), # FIX: Added extraction
            url=article.get('url', ''),
            date=article.get('publishedAt', 'N/A'),
            source=article.get('source', 'Unknown'),
            sentiment=article.get('sentiment', 'Neutral')
        ))

    has_more = offset + limit < len(articles)
    return PaginatedNews(
        items=items,
        has_more=has_more,
        next_offset=(offset + limit) if has_more else None,
        total_returned=len(items)
    )

def format_products_list(products: List[Dict[str, Any]], offset: int = 0, limit: int = 5) -> PaginatedProducts:
    sliced = products[offset : offset + limit]
    items = []

    for i, prod in enumerate(sliced):
        ph_link = clean_ph_link(prod.get('ph_post_link', ''))
        direct_link = clean_ph_link(prod.get('direct_website', ''))
        
        items.append(ProductItem(
            id=offset + i,
            name=prod.get('product_name', 'Unknown'),
            tagline=prod.get('tagline', ''),
            votes=prod.get('votes') or 0,
            category=prod.get('category', 'Tech'),
            ph_link=ph_link,
            direct_link=direct_link if direct_link else None
        ))

    has_more = offset + limit < len(products)
    return PaginatedProducts(
        items=items,
        has_more=has_more,
        next_offset=(offset + limit) if has_more else None,
        total_returned=len(items)
    )

def format_repos_list(repos: List[Dict[str, Any]], offset: int = 0, limit: int = 10) -> PaginatedRepos:
    sliced = repos[offset : offset + limit]
    items = []

    for i, repo in enumerate(sliced):
        name = repo.get('full_name', 'Unknown')
        items.append(RepoItem(
            id=offset + i,
            name=name,
            description=repo.get('description') or "No description available.",
            stars=repo.get('stars', 0),
            forks=repo.get('forks', 0),
            language=repo.get('language', 'Unknown'),
            html_url=repo.get('html_url') or f"https://github.com/{name}"
        ))

    has_more = offset + limit < len(repos)
    return PaginatedRepos(
        items=items,
        has_more=has_more,
        next_offset=(offset + limit) if has_more else None,
        total_returned=len(items)
    )

def format_papers_list(papers: List[Dict[str, Any]], tool_name: str, offset: int = 0, limit: int = 10) -> PaginatedPapers:
    sliced = papers[offset : offset + limit]
    items = []

    for i, paper in enumerate(sliced):
        pdf_url = paper.get('pdf_url', '')
        items.append(PaperItem(
            id=offset + i,
            title=paper.get('title', 'Unknown'),
            authors=paper.get('authors', 'Unknown'),
            date=paper.get('date', 'Unknown'),
            page_url=paper.get('page_url', ''),
            pdf_url=pdf_url if pdf_url != "Not available" else "",
            abstract=paper.get('abstract', 'No abstract available.')
        ))

    has_more = offset + limit < len(papers)
    return PaginatedPapers(
        items=items,
        has_more=has_more,
        next_offset=(offset + limit) if has_more else None,
        total_returned=len(items)
    )

def build_summary_response(text: str, url: str = None, is_fallback: bool = False, header_label: str = None) -> SummaryResult:
    return SummaryResult(
        content=text if text else "No content available.",
        read_more_url=url,
        is_fallback=is_fallback,
        header_label=header_label if is_fallback else None
    )