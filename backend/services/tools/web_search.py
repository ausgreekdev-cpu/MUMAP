import re
import time
from urllib.parse import quote_plus

import httpx

from .base import Tool, ToolResult


class WebSearchTool(Tool):
    name = "web_search"
    description = "Search the web using DuckDuckGo and return relevant results."
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query",
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 5,
            },
        },
        "required": ["query"],
    }

    async def execute(self, query: str, max_results: int = 5, **kwargs) -> ToolResult:
        start = time.monotonic()
        try:
            if not query.strip():
                return ToolResult(
                    success=False,
                    output=None,
                    error="Query cannot be empty",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            encoded_query = quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            }

            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()

            results = self._parse_results(response.text)[:max_results]
            duration = int((time.monotonic() - start) * 1000)

            return ToolResult(
                success=True,
                output=results,
                duration_ms=duration,
                metadata={"query": query, "result_count": len(results)},
            )
        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                output=None,
                error="Search request timed out",
                duration_ms=int((time.monotonic() - start) * 1000),
            )
        except httpx.HTTPStatusError as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"HTTP error: {e.response.status_code}",
                duration_ms=int((time.monotonic() - start) * 1000),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

    def _parse_results(self, html: str) -> list[dict]:
        results = []
        result_pattern = re.compile(
            r'<a[^>]+class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            re.DOTALL,
        )

        for match in result_pattern.finditer(html):
            url = match.group(1).strip()
            title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
            snippet = re.sub(r"<[^>]+>", "", match.group(3)).strip()

            if url and title:
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                })

        if not results:
            simple_pattern = re.compile(
                r'<h2[^>]*class="result__title"[^>]*>.*?<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>',
                re.DOTALL,
            )
            for match in simple_pattern.finditer(html):
                url = match.group(1).strip()
                title = re.sub(r"<[^>]+>", "", match.group(2)).strip()
                if url and title:
                    results.append({
                        "title": title,
                        "url": url,
                        "snippet": "",
                    })

        return results


web_search_tool = WebSearchTool()
