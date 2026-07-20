import ipaddress
import time
from urllib.parse import urlparse

import httpx

from .base import Tool, ToolResult


class HttpRequestTool(Tool):
    name = "http_request"
    description = "Make HTTP requests to external APIs. Blocks internal IP addresses for security."
    parameters = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to send the request to",
            },
            "method": {
                "type": "string",
                "description": "HTTP method (GET, POST, PUT, DELETE, PATCH)",
                "default": "GET",
            },
            "headers": {
                "type": "object",
                "description": "Request headers as key-value pairs",
            },
            "body": {
                "type": "object",
                "description": "Request body as JSON object",
            },
        },
        "required": ["url"],
    }

    TIMEOUT = 30.0
    MAX_RESPONSE_SIZE = 10 * 1024 * 1024
    BLOCKED_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("169.254.0.0/16"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
        ipaddress.ip_network("fe80::/10"),
    ]
    ALLOWED_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}

    async def execute(
        self,
        url: str,
        method: str = "GET",
        headers: dict | None = None,
        body: dict | None = None,
        **kwargs,
    ) -> ToolResult:
        start = time.monotonic()
        try:
            if not url.strip():
                return ToolResult(
                    success=False,
                    output=None,
                    error="URL cannot be empty",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            method_upper = method.upper()
            if method_upper not in self.ALLOWED_METHODS:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Invalid HTTP method: {method}. Allowed: {', '.join(sorted(self.ALLOWED_METHODS))}",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Invalid URL scheme: {parsed.scheme}. Only http and https are allowed.",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            if self._is_blocked_host(parsed.hostname or ""):
                return ToolResult(
                    success=False,
                    output=None,
                    error="Request to internal/private IP address is blocked",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            request_headers = headers or {}
            if body and "Content-Type" not in request_headers and "content-type" not in request_headers:
                request_headers["Content-Type"] = "application/json"

            async with httpx.AsyncClient(
                timeout=self.TIMEOUT,
                follow_redirects=True,
                verify=True,
            ) as client:
                response = await client.request(
                    method=method_upper,
                    url=url,
                    headers=request_headers,
                    json=body,
                )

            content_length = len(response.content)
            if content_length > self.MAX_RESPONSE_SIZE:
                return ToolResult(
                    success=False,
                    output=None,
                    error=f"Response too large: {content_length} bytes",
                    duration_ms=int((time.monotonic() - start) * 1000),
                )

            try:
                response_body = response.json()
            except Exception:
                response_body = response.text

            duration = int((time.monotonic() - start) * 1000)
            return ToolResult(
                success=True,
                output={
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "body": response_body,
                },
                duration_ms=duration,
                metadata={
                    "url": url,
                    "method": method_upper,
                    "content_length": content_length,
                },
            )
        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                output=None,
                error=f"Request timed out after {self.TIMEOUT}s",
                duration_ms=int((time.monotonic() - start) * 1000),
            )
        except httpx.ConnectError as e:
            return ToolResult(
                success=False,
                output=None,
                error=f"Connection failed: {e}",
                duration_ms=int((time.monotonic() - start) * 1000),
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output=None,
                error=str(e),
                duration_ms=int((time.monotonic() - start) * 1000),
            )

    def _is_blocked_host(self, hostname: str) -> bool:
        try:
            resolved = ipaddress.ip_address(hostname)
            for network in self.BLOCKED_NETWORKS:
                if resolved in network:
                    return True
            return False
        except ValueError:
            if hostname in ("localhost", "0.0.0.0", "::"):
                return True
            blocked_domains = ["localhost", "127.0.0.1", "0.0.0.0"]
            if hostname.lower() in blocked_domains:
                return True
            return False


http_request_tool = HttpRequestTool()
