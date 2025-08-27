"""
SearXNG tools for web search
"""
import asyncio
import requests
import json
import urllib.parse
from typing import List, Dict, Any, Optional
from subtools.notify import ntfyClient

class SearXNGTools:
    """Tools for interacting with SearXNG instance"""
    
    def __init__(self, searxng_url: str = "http://localhost:8888", logger=None):
        self.searxng_url = searxng_url.rstrip('/')
        self.logger = logger
    
    def register_tools(self, mcp_server):
        """Register SearXNG tools with the MCP server"""
        
        @mcp_server.tool()
        async def searxng_search(
            query: str,
            categories: List[str] = None,
            engines: List[str] = None,
            language: str = "auto",
            time_range: str = None,
            format: str = "json",
            max_results: int = 20
        ) -> Dict[str, Any]:
            """
            Search using SearXNG instance.
            
            Args:
                query: Search query
                categories: Search categories (general, images, videos, news, music, etc.)
                engines: Specific search engines to use
                language: Search language (auto, en, es, fr, etc.)
                time_range: Time range filter (day, week, month, year)
                format: Output format (json, xml, csv, rss)
                max_results: Maximum number of results
            """
            try:
                return await self._search(query, categories, engines, language, time_range, format, max_results)
            except Exception as e:
                return {"error": f"SearXNG search failed: {str(e)}"}

        @mcp_server.tool()
        async def searxng_suggestions(query: str) -> Dict[str, Any]:
            """
            Get search suggestions from SearXNG.
            
            Args:
                query: Partial query for suggestions
            """
            try:
                return await self._get_suggestions(query)
            except Exception as e:
                return {"error": f"SearXNG suggestions failed: {str(e)}"}

        @mcp_server.tool()
        async def searxng_get_engines() -> Dict[str, Any]:
            """Get list of available search engines from SearXNG instance."""
            try:
                return await self._get_engines()
            except Exception as e:
                return {"error": f"Failed to get SearXNG engines: {str(e)}"}

        @mcp_server.tool()
        async def searxng_get_categories() -> Dict[str, Any]:
            """Get list of available search categories from SearXNG instance."""
            try:
                return await self._get_categories()
            except Exception as e:
                return {"error": f"Failed to get SearXNG categories: {str(e)}"}

        @mcp_server.tool()
        async def searxng_status() -> Dict[str, Any]:
            """Check SearXNG instance status and capabilities."""
            try:
                return await self._get_status()
            except Exception as e:
                return {"error": f"Failed to get SearXNG status: {str(e)}"}

    async def _search(self, query: str, categories: List[str], engines: List[str], language: str, time_range: str, format: str, max_results: int) -> Dict[str, Any]:
        """Perform search using SearXNG"""
        try:
            params = {
                "q": query,
                "format": format,
                "lang": language
            }
            
            if categories:
                params["categories"] = ",".join(categories)
            
            if engines:
                params["engines"] = ",".join(engines)
            
            if time_range:
                params["time_range"] = time_range

            response = requests.get(
                f"{self.searxng_url}/search",
                params=params,
                timeout=30,
                headers={"Accept": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Limit results if specified
                if "results" in data and max_results > 0:
                    data["results"] = data["results"][:max_results]
                
                return {
                    "success": True,
                    "query": query,
                    "data": data,
                    "total_results": len(data.get("results", [])),
                    "searxng_url": self.searxng_url
                }
            else:
                return {"error": f"SearXNG search error: {response.status_code} - {response.text}"}
                
        except requests.exceptions.ConnectionError:
            return {"error": f"Cannot connect to SearXNG instance at {self.searxng_url}. Is it running?"}
        except Exception as e:
            return {"error": f"Search failed: {str(e)}"}

    async def _get_suggestions(self, query: str) -> Dict[str, Any]:
        """Get search suggestions"""
        try:
            params = {
                "q": query,
                "format": "json"
            }

            response = requests.get(
                f"{self.searxng_url}/autocompleter",
                params=params,
                timeout=10,
                headers={"Accept": "application/json"}
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "query": query,
                    "suggestions": response.json(),
                    "searxng_url": self.searxng_url
                }
            else:
                return {"error": f"SearXNG suggestions error: {response.status_code} - {response.text}"}
                
        except requests.exceptions.ConnectionError:
            return {"error": f"Cannot connect to SearXNG instance at {self.searxng_url}"}
        except Exception as e:
            return {"error": f"Suggestions failed: {str(e)}"}

    async def _get_engines(self) -> Dict[str, Any]:
        """Get available search engines"""
        try:
            response = requests.get(
                f"{self.searxng_url}/config",
                timeout=10,
                headers={"Accept": "application/json"}
            )
            
            if response.status_code == 200:
                config = response.json()
                engines = config.get("engines", [])
                
                # Format engine information
                formatted_engines = {}
                for engine_name, engine_info in engines.items():
                    formatted_engines[engine_name] = {
                        "categories": engine_info.get("categories", []),
                        "shortcut": engine_info.get("shortcut", ""),
                        "disabled": engine_info.get("disabled", False),
                        "timeout": engine_info.get("timeout", 0)
                    }
                
                return {
                    "success": True,
                    "engines": formatted_engines,
                    "total_engines": len(formatted_engines),
                    "searxng_url": self.searxng_url
                }
            else:
                return {"error": f"SearXNG config error: {response.status_code} - {response.text}"}
                
        except requests.exceptions.ConnectionError:
            return {"error": f"Cannot connect to SearXNG instance at {self.searxng_url}"}
        except Exception as e:
            return {"error": f"Get engines failed: {str(e)}"}

    async def _get_categories(self) -> Dict[str, Any]:
        """Get available search categories"""
        try:
            response = requests.get(
                f"{self.searxng_url}/config",
                timeout=10,
                headers={"Accept": "application/json"}
            )
            
            if response.status_code == 200:
                config = response.json()
                categories = config.get("categories", {})
                
                return {
                    "success": True,
                    "categories": list(categories.keys()),
                    "category_details": categories,
                    "searxng_url": self.searxng_url
                }
            else:
                return {"error": f"SearXNG config error: {response.status_code} - {response.text}"}
                
        except requests.exceptions.ConnectionError:
            return {"error": f"Cannot connect to SearXNG instance at {self.searxng_url}"}
        except Exception as e:
            return {"error": f"Get categories failed: {str(e)}"}

    async def _get_status(self) -> Dict[str, Any]:
        """Check SearXNG instance status"""
        try:
            # Try to get basic info
            response = requests.get(
                f"{self.searxng_url}/stats",
                timeout=10,
                headers={"Accept": "application/json"}
            )
            
            status_info = {
                "searxng_url": self.searxng_url,
                "available": False,
                "response_time_ms": None
            }
            
            import time
            start_time = time.time()
            
            if response.status_code == 200:
                response_time = (time.time() - start_time) * 1000
                stats = response.json()
                
                status_info.update({
                    "available": True,
                    "response_time_ms": round(response_time, 2),
                    "stats": stats
                })
            else:
                # Try basic health check
                health_response = requests.get(f"{self.searxng_url}/", timeout=5)
                if health_response.status_code == 200:
                    response_time = (time.time() - start_time) * 1000
                    status_info.update({
                        "available": True,
                        "response_time_ms": round(response_time, 2),
                        "note": "Basic health check passed, but stats endpoint unavailable"
                    })
                
            return status_info
                
        except requests.exceptions.ConnectionError:
            return {
                "searxng_url": self.searxng_url,
                "available": False,
                "error": "Connection failed - SearXNG instance may not be running"
            }
        except Exception as e:
            return {
                "searxng_url": self.searxng_url,
                "available": False,
                "error": f"Status check failed: {str(e)}"
            }