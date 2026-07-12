"""Web search via DuckDuckGo's HTML endpoint (no API key required).

Returns lightweight results ({title, url, snippet}) the agent uses when the planner
decides the user's notes are insufficient. Best-effort: any failure returns an empty
list so the turn still completes (just without web grounding).
"""

from __future__ import annotations

from urllib.parse import parse_qs, unquote, urlparse

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings

_ENDPOINT = "https://html.duckduckgo.com/html/"
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
    )
}


def _clean_url(href: str) -> str:
    # DuckDuckGo wraps result links as /l/?uddg=<encoded target>.
    if "uddg=" in href:
        qs = parse_qs(urlparse(href).query)
        if "uddg" in qs:
            return unquote(qs["uddg"][0])
    return href


async def search_web(query: str, *, k: int | None = None) -> list[dict]:
    k = k or settings.web_search_max_results
    try:
        async with httpx.AsyncClient(
            timeout=15.0, headers=_HEADERS, follow_redirects=True
        ) as client:
            resp = await client.post(_ENDPOINT, data={"q": query})
        if resp.status_code >= 400:
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        results: list[dict] = []
        for node in soup.select(".result")[: k * 2]:
            link = node.select_one(".result__a")
            snippet = node.select_one(".result__snippet")
            if not link:
                continue
            results.append(
                {
                    "title": link.get_text(strip=True),
                    "url": _clean_url(link.get("href", "")),
                    "snippet": snippet.get_text(strip=True) if snippet else "",
                }
            )
            if len(results) >= k:
                break
        return results
    except Exception:
        return []
