# mcp_server.py
from mcp.server.fastmcp import FastMCP
import logging
from tnews import TechNewsEngine
from prodhunt import ProductHuntEngine
from arxiv import ArxivService
from git import GitHubService
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("SynapseMCP")

mcp = FastMCP("SynapseIQ_Intelligence_Server")

logger.info("Booting up Data Engines for MCP Server...")
news_engine = TechNewsEngine()
ph_engine = ProductHuntEngine()
arxiv_engine = ArxivService()
github_engine = GitHubService()


@mcp.tool()
async def fetch_tech_news(top_n: int = 5) -> list:
    """
    Fetches the top trending and latest technology, AI, and DevOps news.
    Use this when the user asks for general tech news, AI updates, or tech world happenings.
    
    Args:
        top_n: Number of articles to return (default is 5).
    """
    logger.info(f"MCP Tool Called: fetch_tech_news (top_n={top_n})")
    return await news_engine.get_latest_tech_news(top_n=top_n)


@mcp.tool()
async def fetch_product_hunt_trending() -> list:
    """
    Fetches today's top trending software products, AI tools, and startups from Product Hunt.
    Use this when the user wants to know about new startups, product launches, or trending tools.
    """
    logger.info("MCP Tool Called: fetch_product_hunt_trending")
    products, _ = await ph_engine.get_top_products()
    return products


@mcp.tool()
async def fetch_arxiv_papers(category_key: str = "1", max_results: int = 5) -> list:
    """
    Fetches the latest academic research papers and breakthroughs from ArXiv.
    Use this when the user asks for research papers, academic studies, or deep-tech breakthroughs.
    
    Args:
        category_key: The domain of research. 
                      "1" = Artificial Intelligence, "2" = Machine Learning, 
                      "3" = Computer Vision, "4" = NLP, "5" = Quant Finance, "6" = Security.
        max_results: Number of papers to retrieve (default is 5).
    """
    logger.info(f"MCP Tool Called: fetch_arxiv_papers (category={category_key}, max={max_results})")
    return await arxiv_engine.get_latest_papers(category_key, max_results)


@mcp.tool()
async def search_arxiv_papers(keyword: str, max_results: int = 5) -> list:
    """
    Searches ArXiv for specific academic research papers based on a keyword.
    Use this when the user asks for research papers on a very specific topic (e.g., 'transformers', 'LLM routing').
    
    Args:
        keyword: The specific topic or keyword to search for.
        max_results: Number of papers to retrieve (default is 5).
    """
    logger.info(f"MCP Tool Called: search_arxiv_papers (keyword='{keyword}', max={max_results})")
    return await arxiv_engine.search_papers(keyword, max_results)


@mcp.tool()
async def fetch_github_trending(category_key: str = "1") -> list:
    """
    Fetches trending open-source GitHub repositories based on domains.
    Use this when the user asks for trending repos, open-source projects, or developer tools.
    
    Args:
        category_key: The developer domain.
                      "1" = AI & Machine Learning, "2" = Web Development, 
                      "3" = Backend & API, "4" = Databases, 
                      "5" = DevOps & Cloud, "6" = UI / UX Frameworks.
    """
    logger.info(f"MCP Tool Called: fetch_github_trending (category={category_key})")
    return await github_engine.get_trending_repos(category_key)

@mcp.tool()
async def fetch_github_readme(full_name: str) -> str:
    """
    Fetches the raw README markdown content for a specific GitHub repository.
    Use this when the user asks for a deep summary or explanation of a specific repo.
    
    Args:
        full_name: The full repository name (e.g., 'synapse/iq_bot').
    """
    logger.info(f"MCP Tool Called: fetch_github_readme (repo='{full_name}')")
    return await github_engine.get_readme_content(full_name)

if __name__ == "__main__":
    # Runs the MCP server via standard input/output (STDIO) which is perfect for local LLM integration
    logger.info("SynapseIQ MCP Server is up and running via STDIO!")
    mcp.run()