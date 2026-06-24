import re

import httpx
from duckduckgo_search import DDGS


def search_web(query: str) -> list[dict]:
    """Search the web using DuckDuckGo — no API key needed."""
    with DDGS() as ddgs:
        results = ddgs.text(query, max_results=5)
    return [
        {"title": r["title"], "url": r["href"], "content": r["body"]}
        for r in results
    ]


def fetch_page(url: str) -> str:
    """Fetch the text content of a web page, stripping HTML tags."""
    try:
        response = httpx.get(url, timeout=10, follow_redirects=True)
        response.raise_for_status()
        text = response.text
        # Remove script and style blocks entirely
        text = re.sub(r"<(script|style)[^>]*>.*?</(script|style)>", "", text, flags=re.DOTALL | re.IGNORECASE)
        # Strip remaining HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        # Collapse whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text[:8000]  # Cap at 8k chars to keep context manageable
    except Exception as e:
        return f"Error fetching page: {e}"


# JSON schemas that describe each tool to Claude.
# Claude reads these to know what tools exist and how to call them.
TOOL_SCHEMAS = [
    {
        "name": "search_web",
        "description": (
            "Search the web for information on a topic. "
            "Returns a list of results with titles, URLs, and content snippets."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_page",
        "description": (
            "Fetch the full text content of a web page by URL. "
            "Use this to get detailed information from a specific source found via search."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the web page to fetch",
                }
            },
            "required": ["url"],
        },
    },
]
