# 🧠 ProtoMind.ai

> **A Full-Stack AI Tech-Intelligence Hub & FastMCP Server.**
> ProtoMind.ai bridges real-time technology streams — global tech news, startup launches, academic papers, and GitHub repositories — into a single, cyberpunk-themed dashboard powered by an autonomous dual-LLM routing engine.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![FastMCP](https://img.shields.io/badge/FastMCP-Protocol-8b5cf6)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🚀 Overview

ProtoMind.ai is built around a **dual-interface architecture**, so the same intelligence engines can serve both humans and other AI agents:

1. **Human Interface (B2C)** — A responsive, neon-cyberpunk web dashboard where users chat with **ProtoAI** to fetch, summarize, and explore live tech data (news, products, papers, repos) through interactive UI cards.
2. **Machine-to-Machine Interface (M2M)** — A headless **FastMCP** server (`mcpserver.py`) that exposes the same data engines as tools to external AI agents (e.g. Claude Desktop) over the Model Context Protocol via STDIO.

Both interfaces sit on top of the same set of independent, cache-aware data engines, so results stay consistent whether they're requested from the dashboard or from an MCP client.

---

## ✨ Key Features

### 🤖 Dual-Cloud AI Routing Engine (`llmengine.py`)
- **Smart Fallback:** Every LLM call first attempts **Gemini** (`gemini-3.5-flash-lite`), then transparently falls back to **Groq** (`qwen3.6-27b`) via [LiteLLM](https://github.com/BerriAI/litellm) if a provider is unavailable, rate-limited, or times out.
- **Autonomous Tool Selection:** A routing system prompt maps free-text user queries to the correct backend engine (news, Product Hunt, ArXiv, GitHub) and extracts the right arguments — no manual intent classification needed.
- **AI Summarization:** The same dual-provider pipeline powers on-demand summaries (e.g. GitHub README digests) with graceful degradation to a raw excerpt if both providers fail.

### 🌐 Neural Feeds (Data Engines)
| Engine | File | What it does |
|---|---|---|
| **Daily Tech Digest** | `tnews.py` | Aggregates tech/AI/DevOps news concurrently from Google News, TechCrunch, and Economic Times RSS feeds, deduplicates them, and ranks them using a keyword-signal scorer (8 topic domains) blended with VADER sentiment analysis and per-source credibility weighting. |
| **Product Radar** | `prodhunt.py` | Fetches daily trending products/startups from the Product Hunt GraphQL API, with an automatic fallback to the public RSS feed (and HTML/UTM-cleaned taglines) if the API token is missing or rate-limited. |
| **GitHub Intelligence** | `git.py`, `config.py` | Surfaces **Trending Repos** by domain (AI/ML, Web, Backend, Databases, DevOps, UI/UX) within a rolling 90-day window, a curated list of **Industry Giants** per domain (no API calls needed), an ad-hoc **repo search**, and raw **README** fetching for AI summarization. Uses `TTLCache` for trending/search/detail results and gracefully handles GitHub's rate-limit headers. |
| **Research Papers (ArXiv)** | `arxiv.py` | Fetches and searches the latest academic papers across 6 domains (AI, ML, Computer Vision, NLP, Quant Finance, Cryptography/Security) directly from the ArXiv Atom API, with rate-limiting, XML parsing, and per-endpoint TTL caching. |

### 🖥️ Cyberpunk UI/UX (`index.html`, `style.css`, `script.js`)
- Deep space navy/black aesthetic (`#020617`) with dynamic cyan (`#0ea5e9`) and purple neon glows.
- Smooth CSS backdrop blur, gradients, and blend modes for an immersive background.
- Collapsible sidebar, tabbed navigation (News / Products / GitHub / ArXiv), a chat interface routed through ProtoAI, and modal views for reading paper abstracts.
- Standalone HTML5/CSS3/vanilla JS frontend — no build step or framework required.

### 🔌 Model Context Protocol (MCP) Server
- Exposes 6 tools over STDIO: `fetch_tech_news`, `fetch_product_hunt_trending`, `fetch_arxiv_papers`, `search_arxiv_papers`, `fetch_github_trending`, `fetch_github_readme`.
- Lets any MCP-compatible AI client (Claude Desktop, etc.) query ProtoMind's live data engines directly as tools, independent of the web dashboard.

---

## 🏗️ Architecture Stack

- **Backend:** FastAPI (Python), Uvicorn
- **AI / LLM Routing:** LiteLLM (Gemini + Groq, with automatic fallback)
- **Agent Protocol:** FastMCP (Model Context Protocol) over STDIO
- **Data Integrations:** Asynchronous engines built on `httpx`, `feedparser`, and `BeautifulSoup`
- **NLP:** VADER Sentiment Analysis for news scoring
- **Caching:** In-memory TTL caching (`TTLCache` / custom TTL dicts) per engine to reduce redundant API calls and respect provider rate limits
- **Frontend:** Vanilla HTML5, CSS3, JavaScript (no framework)

---

## 📂 Project Structure

```
ProtoMind.ai/
├── main.py              # FastAPI application, REST endpoints, and LLM-driven /api/query router
├── llmengine.py          # Dual-cloud LLM routing (Gemini → Groq fallback) and summarization logic
├── mcpserver.py          # FastMCP server exposing tools to external AI agents over STDIO
├── formatters.py         # Pydantic response models and pagination/formatting helpers
├── config.py              # GitHub domain definitions and curated "Industry Giants" repo lists
├── tnews.py               # Tech news aggregation, scoring, and sentiment engine
├── prodhunt.py            # Product Hunt GraphQL + RSS fallback engine
├── git.py                 # GitHub trending, curated, search, and README engine
├── arxiv.py                # ArXiv research paper discovery and search engine
├── index.html              # Frontend UI
├── style.css               # Cyberpunk & neon styling
├── script.js                # Frontend logic and API integration
└── .env                      # Environment variables (ignored in Git)
```

---

## ⚙️ Installation & Setup

### 1. Clone the Repository
```bash
git clone git@github.com:Jai0406/ProtoMind.ai.git
cd ProtoMind.ai
```

### 2. Set Up a Virtual Environment
```bash
python -m venv myvenv

# Windows
myvenv\Scripts\activate

# macOS / Linux
source myvenv/bin/activate
```

### 3. Install Dependencies
```bash
pip install fastapi uvicorn litellm httpx beautifulsoup4 python-dotenv fastmcp \
            feedparser vaderSentiment cachetools
```

### 4. Configure Environment Variables
Create a `.env` file in the project root:

```env
# AI Providers
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini/gemini-3.5-flash-lite      # optional override
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=groq/qwen/qwen3.6-27b               # optional override
CLOUD_LLM_TIMEOUT=15                            # optional, seconds

# Product Hunt (optional — falls back to RSS if omitted)
PRODUCTHUNT_DEV_TOKEN=your_producthunt_token_here

# GitHub (optional but strongly recommended: 60 → 5000 req/hr)
GITHUB_TOKEN=your_github_personal_access_token
```

---

## 💻 Usage

### Running the Web Dashboard (FastAPI)
```bash
uvicorn main:app --port 8000 --reload
```
Once the server logs `Application startup complete`, open `index.html` in any modern browser to access the ProtoMind.ai dashboard.

### Running as an MCP Server
To let an external LLM client (e.g. Claude Desktop) use ProtoMind's tools directly:
```bash
python mcpserver.py
```
The server communicates over STDIO, so it should be launched by the MCP client's configuration rather than run standalone in a terminal for interactive use.

---

## 🔗 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/query` | Natural-language query → routed to the correct engine by the dual-LLM router |
| `GET` | `/api/news` | Paginated latest tech news |
| `GET` | `/api/products` | Paginated Product Hunt trending products |
| `GET` | `/api/github/trending` | Trending GitHub repos by domain (`category_key`) |
| `GET` | `/api/github/curated` | Curated "Industry Giants" repos by domain |
| `GET` | `/api/github/search` | GitHub repo search by keyword |
| `GET` | `/api/github/readme` | AI-summarized README for a given repo |
| `GET` | `/api/arxiv/latest` | Latest ArXiv papers by domain |
| `GET` | `/api/arxiv/search` | ArXiv paper search by keyword |
| `POST` | `/api/summarize` | Generic AI summary of arbitrary text |
| `GET` | `/health` | Health check |

Full request/response schemas are defined via Pydantic models in `formatters.py` and enforced automatically by FastAPI (see `/docs` for interactive Swagger UI once the server is running).

---

## 🛠️ Engineering Notes

- **Resilience by design:** every external data source has an explicit fallback path — Product Hunt drops from GraphQL to RSS, tech news pulls from three independent RSS sources concurrently, and LLM calls cascade across providers instead of failing outright.
- **Rate-limit awareness:** GitHub and ArXiv engines both track and respect provider-imposed limits (GitHub's `X-RateLimit-*` headers, ArXiv's recommended 3-second request delay).
- **Caching strategy:** each engine uses TTL caching tuned to how often its underlying data actually changes (10 min for news, 1 hr for Product Hunt/ArXiv latest, 12 hr for GitHub trending), minimizing redundant calls while keeping data fresh.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

**Built by Jai.**