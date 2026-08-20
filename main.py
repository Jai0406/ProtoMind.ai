
import json
import logging
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi import Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from tnews import TechNewsEngine
from prodhunt import ProductHuntEngine
from arxiv import ArxivService
from git import GitHubService
from llmengine import route_query, summarize
from formatters import (
    format_news_list, format_products_list, format_repos_list, format_papers_list,
    build_summary_response,
    PaginatedNews, PaginatedProducts, PaginatedRepos, PaginatedPapers, SummaryResult,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SynapseBackend")

class QueryRequest(BaseModel):
    user_text: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.news_engine = TechNewsEngine()
    app.state.ph_engine = ProductHuntEngine()
    app.state.arxiv_engine = ArxivService()
    app.state.github_engine = GitHubService()
    
    await app.state.ph_engine.start()
    await app.state.github_engine.start()
    yield

    logger.info("Shutting down... Closing all HTTPX clients.")
    await app.state.arxiv_engine.close()
    await app.state.ph_engine.close()
    await app.state.github_engine.close()

# Dependency Functions (Endpoints me use karne ke liye)
def get_news_engine(request: Request): return request.app.state.news_engine
def get_ph_engine(request: Request): return request.app.state.ph_engine
def get_github_engine(request: Request): return request.app.state.github_engine
def get_arxiv_engine(request: Request): return request.app.state.arxiv_engine

app = FastAPI(title="SynapseIQ Backend", version="1.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],)

ROUTING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "fetch_tech_news",
            "description": "Fetches the top trending and latest technology, AI, and DevOps news.",
            "parameters": {
                "type": "object",
                "properties": {
                    "top_n": {"type": "integer", "description": "Number of articles to return", "default": 150}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_product_hunt_trending",
            "description": "Fetches today's top trending software products, AI tools, and startups from Product Hunt.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_arxiv_papers",
            "description": "Fetches the latest academic research papers from ArXiv for a given domain.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category_key": {
                        "type": "string",
                        "description": "1=AI, 2=ML, 3=Computer Vision, 4=NLP, 5=Quant Finance, 6=Security",
                        "enum": ["1", "2", "3", "4", "5", "6"]
                    },
                    "max_results": {"type": "integer", "default": 5},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_arxiv_papers",
            "description": "Searches ArXiv for research papers matching a specific keyword.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string"},
                    "max_results": {"type": "integer", "default": 5},
                },
                "required": ["keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_github_trending",
            "description": "Fetches trending open-source GitHub repositories. ONLY use this if the user specifies a domain (e.g., AI, Web, DevOps). If domain is unspecified, DO NOT call this tool; ask the user to choose a domain.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category_key": {
                        "type": "string",
                        "description": "1=AI/ML, 2=Web Dev, 3=Backend/API, 4=Databases, 5=DevOps/Cloud, 6=UI/UX",
                        "enum": ["1", "2", "3", "4", "5", "6"]
                    }
                },
                "required": ["category_key"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_github_repos",
            "description": "Searches GitHub for repositories matching a specific keyword or topic.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "The search query, e.g., 'react', 'fastapi'"}
                },
                "required": ["keyword"],
            },
        },
    },
]

@app.post("/api/query")
async def query(request: Request, query_req: QueryRequest):
    response = await route_query(query_req.user_text, ROUTING_TOOLS)
    if response is None:
        raise HTTPException(status_code=503, detail="Both LLM providers are currently unavailable.")

    model_used = getattr(response, "model", "Unknown Model")
    choice = response.choices[0].message
    tool_calls = getattr(choice, "tool_calls", None)

    if not tool_calls:
        return {"type": "text", "content": choice.content, "routed_by_llm": model_used}

    call = tool_calls[0]
    tool_name = call.function.name
    args = json.loads(call.function.arguments or "{}")

    state = request.app.state
    
    try:
        if tool_name == "fetch_tech_news":
            result = await state.news_engine.get_latest_tech_news(top_n=args.get("top_n", 150))
        elif tool_name == "fetch_product_hunt_trending":
            result, _ = await state.ph_engine.get_top_products()
        elif tool_name == "fetch_arxiv_papers":
            result = await state.arxiv_engine.get_latest_papers(args.get("category_key", "1"), args.get("max_results", 5))
        elif tool_name == "search_arxiv_papers":
            result = await state.arxiv_engine.search_papers(args["keyword"], args.get("max_results", 5))
        elif tool_name == "fetch_github_trending":
            result = await state.github_engine.get_trending_repos(args.get("category_key", "1"))
        elif tool_name == "search_github_repos":
            result = await state.github_engine.search_repositories(args["keyword"])
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool routed: {tool_name}")
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "type": "tool_result",
        "tool": tool_name,
        "routed_by_llm": model_used,
        "args": args,
        "data": result
    }

@app.get("/api/news", response_model=PaginatedNews)
async def get_news(
    offset: int = 0, 
    limit: int = 1000, 
    top_n: Optional[int] = None,
    engine: TechNewsEngine = Depends(get_news_engine)
):
    articles = await engine.get_latest_tech_news(top_n=top_n)
    return format_news_list(articles, offset=offset, limit=limit)

@app.get("/api/products", response_model=PaginatedProducts)
async def get_products(
    offset: int = 0, 
    limit: int = 1000,
    engine: ProductHuntEngine = Depends(get_ph_engine)
):
    products, _source = await engine.get_top_products()
    return format_products_list(products, offset=offset, limit=limit)

@app.get("/api/github/trending", response_model=PaginatedRepos)
async def get_github_trending(
    category_key: str = "1", 
    offset: int = 0, 
    limit: int = 1000,
    engine: GitHubService = Depends(get_github_engine)
):
    repos = await engine.get_trending_repos(category_key)
    return format_repos_list(repos, offset=offset, limit=limit)


@app.get("/api/github/readme", response_model=SummaryResult)
async def get_github_readme(
    full_name: str,
    engine: GitHubService = Depends(get_github_engine)
):
    readme_text = await engine.get_readme_content(full_name)
    summary = await summarize(readme_text, label=f"the README of {full_name}")
    repo_url = f"https://github.com/{full_name}"

    if summary:
        return build_summary_response(summary, url=repo_url)
    return build_summary_response(
        readme_text, url=repo_url,
        is_fallback=True, header_label="Excerpt (AI summary unavailable):"
    )

@app.get("/api/arxiv/latest", response_model=PaginatedPapers)
async def get_arxiv_latest(
    category_key: str = "1", 
    offset: int = 0, 
    limit: int = 1000, 
    max_results: int = 100,
    engine: ArxivService = Depends(get_arxiv_engine)
):
    papers = await engine.get_latest_papers(category_key, max_results)
    return format_papers_list(papers, tool_name="fetch_arxiv_papers", offset=offset, limit=limit)

@app.get("/api/arxiv/search", response_model=PaginatedPapers)
async def search_arxiv(
    keyword: str, 
    offset: int = 0, 
    limit: int = 1000, 
    max_results: int = 100,
    engine: ArxivService = Depends(get_arxiv_engine)
):
    papers = await engine.search_papers(keyword, max_results)
    return format_papers_list(papers, tool_name="search_arxiv_papers", offset=offset, limit=limit)

@app.post("/api/summarize", response_model=SummaryResult)
async def summarize_item(text: str, label: str, url: Optional[str] = None):
    result = await summarize(text, label)
    if result:
        return build_summary_response(result, url=url)
    return build_summary_response(
        text, url=url, is_fallback=True, header_label="Excerpt (AI summary unavailable):"
    )

@app.get("/api/github/curated", response_model=PaginatedRepos)
async def get_github_curated(
    category_key: str = "1", 
    offset: int = 0, 
    limit: int = 1000,
    engine: GitHubService = Depends(get_github_engine)
):
    from config import CURATED_STANDARDS
    if category_key not in CURATED_STANDARDS:
        raise HTTPException(status_code=400, detail="Invalid curated category key")
    repo_list = [item["repo"] for item in CURATED_STANDARDS[category_key]["items"]]
    
    repos = await engine.get_curated_details(repo_list)
    return format_repos_list(repos, offset=offset, limit=limit)

@app.get("/api/github/search", response_model=PaginatedRepos)
async def search_github(
    keyword: str, 
    offset: int = 0, 
    limit: int = 1000,
    engine: GitHubService = Depends(get_github_engine)
):
    repos = await engine.search_repositories(keyword)
    return format_repos_list(repos, offset=offset, limit=limit)

@app.get("/health")
async def health():
    return {"status": "ok"}