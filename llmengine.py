import os
import logging
import asyncio
from dotenv import load_dotenv
import litellm

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("LLMEngine")


GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini/gemini-3.5-flash-lite")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "groq/qwen/qwen3.6-27b")

CLOUD_LLM_TIMEOUT = int(os.getenv("CLOUD_LLM_TIMEOUT", 15))

PROVIDER_ORDER = ["gemini", "groq"]

_PROVIDER_CONFIG = {
    "gemini": {
        "key": GEMINI_API_KEY,
        "model": GEMINI_MODEL
    },
    "groq": {
        "key": GROQ_API_KEY,
        "model": GROQ_MODEL
    }
}


ROUTING_SYSTEM_PROMPT = (
    "You are SynapseIQ, a routing assistant for a web-based tech-intelligence dashboard. "
    "Your only job is to pick the correct tool for the user's request (tech news, "
    "Product Hunt trends, ArXiv papers, GitHub trending repos, or a GitHub README "
    "summary) and fill in its arguments from the user's message. Don't answer from "
    "memory — your own knowledge is stale, always use a tool when the request "
    "matches one. If nothing matches, reply normally in plain text."
)

SUMMARY_SYSTEM_PROMPT = (
    "You write short, clear summaries (4-6 sentences) for UI cards in a web dashboard. "
    "Plain language, no markdown headers, no preamble like 'Here is a summary'."
)

async def _try_provider(provider_name: str, messages: list, tools: list = None):
    """
    Internal helper to attempt an LLM call with a specific provider.
    Fails gracefully and returns None if the key is missing or the API crashes.
    """
    config = _PROVIDER_CONFIG.get(provider_name)
    
    if not config or not config["key"]:
        logger.warning(f"Skipping '{provider_name}' — API key not found in environment.")
        return None

    model_name = config["model"]
    logger.info(f"Attempting LLM call via '{provider_name}' (Model: {model_name})")

    try:
        response = await litellm.acompletion(
            model=model_name,
            messages=messages,
            tools=tools,
            timeout=CLOUD_LLM_TIMEOUT
        )
        
        if not response or not hasattr(response, 'choices') or not response.choices:
            logger.warning(f"Provider '{provider_name}' returned empty or malformed choices.")
            return None
            
        return response
    except Exception as e:
        logger.warning(f"Provider '{provider_name}' failed. Error: {e}")
        return None


async def route_query(user_text: str, tools: list):
    """
    Routes natural language text to the appropriate tool.
    Loops through PROVIDER_ORDER. Returns the litellm response, or None if all fail.
    """
    messages = [
        {"role": "system", "content": ROUTING_SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]

    for provider in PROVIDER_ORDER:
        result = await _try_provider(provider, messages, tools)
        if result is not None:
            return result
            
    logger.error("All LLM providers failed for route_query. Returning None.")
    return None


async def summarize(text: str, label: str) -> str:
    """
    Generates a summary of the provided text.
    Loops through PROVIDER_ORDER. Returns the summary string, or None if all fail.
    """
    if not text or not text.strip():
        return f"No content available to summarize for {label}."

    messages = [
        {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
        {"role": "user", "content": f"Summarize {label} based on this content:\n\n{text}"},
    ]

    for provider in PROVIDER_ORDER:
        result = await _try_provider(provider, messages, tools=None)
        if result and result.choices and result.choices[0].message.content:
            return result.choices[0].message.content
            
    logger.error("All LLM providers failed for summarize. Returning None.")
    return None