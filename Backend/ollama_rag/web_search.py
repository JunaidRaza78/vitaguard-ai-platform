from duckduckgo_search import DDGS
import logging

logger = logging.getLogger(__name__)

def duckduckgo_medical_search(query: str, max_results: int = 5) -> str:
    """
    DuckDuckGo medical web search (fallback).
    Returns combined text snippets.
    """
    snippets = []

    try:
        with DDGS() as ddgs:
            results = ddgs.text(
                query + " medical information",
                max_results=max_results
            )

            for r in results:
                if r.get("body"):
                    snippets.append(r["body"])

    except Exception as e:
        logger.error(f"DuckDuckGo search failed: {e}")

    return "\n\n".join(snippets[:3])
