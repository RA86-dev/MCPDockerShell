"""
Firecrawl tools for web scraping and crawling
"""
import asyncio
import requests
import json
from typing import List, Dict, Any, Optional

# Optional import - Firecrawl won't be required
try:
    from firecrawl import FirecrawlApp
    HAS_FIRECRAWL = True
except ImportError:
    HAS_FIRECRAWL = False


class FirecrawlTools:
    """Tools for interacting with Firecrawl (local and API)"""

    def __init__(self, logger=None, local_url="http://localhost:3002",api_key=None):
        self.logger = logger
        self.api_key = api_key
        self._firecrawl_local_url = local_url  # Default local Firecrawl URL

    def register_tools(self, mcp_server):
        """Register Firecrawl tools with the MCP server"""

        @mcp_server.tool()
        async def firecrawl_scrape(
            url: str,
            use_local: bool = False,
            formats: List[str] = ["markdown"],
            include_tags: List[str] = None,
            exclude_tags: List[str] = None,
            only_main_content: bool = True,
            timeout: int = 30000
        ) -> Dict[str, Any]:
            api_key = self.api_key
            """
            Scrape a single URL using Firecrawl (local or API).

            Args:
                url: The URL to scrape
                use_local: Whether to use local Firecrawl instance
                formats: Output formats (markdown, html, rawHtml, links, screenshot)
                include_tags: HTML tags to include
                exclude_tags: HTML tags to exclude
                only_main_content: Extract only main content
                timeout: Timeout in milliseconds
            """
            try:
                if use_local:
                    return await self._local_scrape(url, formats, include_tags, exclude_tags, only_main_content, timeout)
                else:
                    if not api_key:
                        return {"error": "API key required for public Firecrawl API"}
                    return await self._api_scrape(url, api_key, formats, include_tags, exclude_tags, only_main_content, timeout)
            except Exception as e:
                return {"error": f"Firecrawl scrape failed: {str(e)}"}

        @mcp_server.tool()
        async def firecrawl_crawl(
            url: str,
            use_local: bool = False,
            max_pages: int = 10,
            formats: List[str] = ["markdown"],
            include_paths: List[str] = None,
            exclude_paths: List[str] = None,
            timeout: int = 60000
        ) -> Dict[str, Any]:
            """
            Crawl multiple pages from a website using Firecrawl.

            Args:
                url: The base URL to crawl

                use_local: Whether to use local Firecrawl instance
                max_pages: Maximum number of pages to crawl
                formats: Output formats
                include_paths: URL patterns to include
                exclude_paths: URL patterns to exclude
                timeout: Timeout in milliseconds
            """
            api_key = self.api_key

            try:
                if use_local:
                    return await self._local_crawl(url, max_pages, formats, include_paths, exclude_paths, timeout)
                else:
                    if not api_key:
                        return {"error": "API key required for public Firecrawl API"}
                    return await self._api_crawl(url, api_key, max_pages, formats, include_paths, exclude_paths, timeout)
            except Exception as e:
                return {"error": f"Firecrawl crawl failed: {str(e)}"}

        @mcp_server.tool()
        async def firecrawl_status() -> Dict[str, Any]:
            """Check if Firecrawl services are available"""
            status = {
                "firecrawl_py_available": HAS_FIRECRAWL,
                "local_instance": await self._check_local_instance(),
                "supported_formats": ["markdown", "html", "rawHtml", "links", "screenshot"]
            }
            return status

    async def _local_scrape(self, url: str, formats: List[str], include_tags: List[str], exclude_tags: List[str], only_main_content: bool, timeout: int) -> Dict[str, Any]:
        """Scrape using local Firecrawl instance"""
        try:
            payload = {
                "url": url,
                "formats": formats,
                "onlyMainContent": only_main_content,
                "timeout": timeout
            }

            if include_tags:
                payload["includeTags"] = include_tags
            if exclude_tags:
                payload["excludeTags"] = exclude_tags

            response = requests.post(
                f"{self._firecrawl_local_url}/v0/scrape",
                json=payload,
                timeout=timeout/1000
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Local Firecrawl error: {response.status_code} - {response.text}"}

        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to local Firecrawl instance. Is it running on port 3002?"}
        except Exception as e:
            return {"error": f"Local scrape failed: {str(e)}"}

    async def _api_scrape(self, url: str, api_key: str, formats: List[str], include_tags: List[str], exclude_tags: List[str], only_main_content: bool, timeout: int) -> Dict[str, Any]:
        """Scrape using Firecrawl API"""
        if not HAS_FIRECRAWL:
            return {"error": "firecrawl-py package not installed. Install with: pip install firecrawl-py"}

        try:
            app = FirecrawlApp(api_key=api_key)

            params = {
                "formats": formats,
                "onlyMainContent": only_main_content,
                "timeout": timeout
            }

            if include_tags:
                params["includeTags"] = include_tags
            if exclude_tags:
                params["excludeTags"] = exclude_tags

            result = app.scrape_url(url, params)
            return {"success": True, "data": result}

        except Exception as e:
            return {"error": f"API scrape failed: {str(e)}"}

    async def _local_crawl(self, url: str, max_pages: int, formats: List[str], include_paths: List[str], exclude_paths: List[str], timeout: int) -> Dict[str, Any]:
        """Crawl using local Firecrawl instance"""
        try:
            payload = {
                "url": url,
                "formats": formats,
                "limit": max_pages,
                "timeout": timeout
            }

            if include_paths:
                payload["includePaths"] = include_paths
            if exclude_paths:
                payload["excludePaths"] = exclude_paths

            response = requests.post(
                f"{self._firecrawl_local_url}/v0/crawl",
                json=payload,
                timeout=timeout/1000
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Local Firecrawl error: {response.status_code} - {response.text}"}

        except requests.exceptions.ConnectionError:
            return {"error": "Cannot connect to local Firecrawl instance. Is it running on port 3002?"}
        except Exception as e:
            return {"error": f"Local crawl failed: {str(e)}"}

    async def _api_crawl(self, url: str, api_key: str, max_pages: int, formats: List[str], include_paths: List[str], exclude_paths: List[str], timeout: int) -> Dict[str, Any]:
        """Crawl using Firecrawl API"""
        if not HAS_FIRECRAWL:
            return {"error": "firecrawl-py package not installed. Install with: pip install firecrawl-py"}

        try:
            app = FirecrawlApp(api_key=api_key)

            params = {
                "formats": formats,
                "limit": max_pages,
                "timeout": timeout
            }

            if include_paths:
                params["includePaths"] = include_paths
            if exclude_paths:
                params["excludePaths"] = exclude_paths

            result = app.crawl_url(url, params)
            return {"success": True, "data": result}

        except Exception as e:
            return {"error": f"API crawl failed: {str(e)}"}

    async def _check_local_instance(self) -> Dict[str, Any]:
        """Check if local Firecrawl instance is available"""
        try:
            response = requests.get(f"{self._firecrawl_local_url}/health", timeout=5)
            return {
                "available": response.status_code == 200,
                "url": self._firecrawl_local_url,
                "status": response.status_code
            }
        except Exception:
            return {
                "available": False,
                "url": self._firecrawl_local_url,
                "error": "Connection failed"
            }
