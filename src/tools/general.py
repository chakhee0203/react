import os
import time
import requests
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool

# 1. Web Search Tool (robust, with fallbacks)
@tool
def web_search(query: str, max_results: int = 5) -> str:
    """Search the web and return concise results. Tries Tavily (if API key), then SerpAPI, then DuckDuckGo.
    Environment variables:
    - TAVILY_API_KEY (optional)
    - SERPAPI_API_KEY (optional)
    """
    tavily_key = os.environ.get("TAVILY_API_KEY")
    serp_key = os.environ.get("SERPAPI_API_KEY")

    try:
        if tavily_key:
            resp = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": query,
                    "search_depth": "advanced",
                    "max_results": max_results,
                },
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("results", [])
            lines = []
            for r in results[:max_results]:
                title = r.get("title", "")
                url = r.get("url", "")
                snippet = r.get("content", "")
                lines.append(f"- {title}\n{url}\n{snippet}")
            return "\n\n".join(lines) or "No results found."

        if serp_key:
            resp = requests.get(
                "https://serpapi.com/search.json",
                params={"q": query, "engine": "google", "api_key": serp_key},
                timeout=20,
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get("organic_results", [])
            lines = []
            for r in results[:max_results]:
                title = r.get("title", "")
                url = r.get("link", "")
                snippet = r.get("snippet", "")
                lines.append(f"- {title}\n{url}\n{snippet}")
            return "\n\n".join(lines) or "No results found."

        # Fallback to DuckDuckGo
        from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
        
        errors = []
        # Try different backends: "api" (default), "html", "lite"
        for backend in ["api", "html", "lite"]:
            try:
                wrapper = DuckDuckGoSearchAPIWrapper(max_results=max_results, backend=backend)
                result = wrapper.run(query)
                if result:
                    return result
            except Exception as e:
                errors.append(f"{backend}: {str(e)}")
                continue
        
        return f"No results found via DuckDuckGo. Errors: {'; '.join(errors)}. Please configure TAVILY_API_KEY or SERPAPI_API_KEY for robust search."
    except Exception as e:
        return f"Search error: {str(e)}"

# 2. Calculator Tool
@tool
def calculator(expression: str) -> str:
    """Calculates the result of a mathematical expression."""
    try:
        return str(eval(expression))
    except Exception as e:
        return f"Error calculating: {str(e)}"

# 3. Time Tool
@tool
def current_time() -> str:
    """Returns the current local time."""
    return time.strftime("%Y-%m-%d %H:%M:%S")
