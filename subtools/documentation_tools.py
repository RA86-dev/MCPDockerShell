"""
Documentation access and management tools
"""

import json
import requests
import os
from typing import Dict, Any, List, Optional
from pathlib import Path


class DocumentationTools:
    """Documentation access and search functionality"""

    def __init__(
        self, docs_dir: Path, devdocs_url: str = "http://localhost:9292", logger=None
    ):
        self.docs_dir = docs_dir
        self.devdocs_url = devdocs_url.rstrip("/")
        self.logger = logger
        self.supported_languages = self._load_language_config()

    def _load_language_config(self) -> Dict[str, Any]:
        """Load supported languages from JSON config file"""
        try:
            config_path = Path(__file__).parent.parent / "documentation_config.json"
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("supported_languages", {})
        except (FileNotFoundError, json.JSONDecodeError) as e:
            if self.logger:
                self.logger.error(f"Error loading language config: {e}")
            return {}

    def register_tools(self, mcp_server):
        """Register documentation tools with the MCP server"""

        @mcp_server.tool()
        async def search_devdocs(
            query: str, language: str = None, max_results: int = 10
        ) -> str:
            """Search through DevDocs documentation"""
            try:
                search_url = f"{self.devdocs_url}/search"
                params = {"q": query, "limit": max_results}
                if language and language in self.supported_languages:
                    params["docs"] = self.supported_languages[language]["devdocs_slug"]

                response = requests.get(search_url, params=params, timeout=30)
                response.raise_for_status()
                results = response.json()
                return json.dumps({"results": results}, indent=2)

            except requests.exceptions.RequestException as e:
                if self.logger:
                    self.logger.error(f"DevDocs search failed: {e}")
                return json.dumps({"error": f"Failed to connect to DevDocs: {e}"})
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in search_devdocs: {e}")
                return json.dumps({"error": str(e)})

        @mcp_server.tool()
        async def get_devdocs_content(path: str, language: str = None) -> str:
            """Get the full content of a specific documentation page from DevDocs"""
            try:
                if language and language in self.supported_languages:
                    doc_slug = self.supported_languages[language]["devdocs_slug"]
                    content_url = f"{self.devdocs_url}/docs/{doc_slug}/{path.lstrip('/')}"
                else:
                    content_url = f"{self.devdocs_url}/docs/{path.lstrip('/')}"

                response = requests.get(content_url, timeout=30)
                response.raise_for_status()
                return json.dumps(response.json(), indent=2)

            except requests.exceptions.RequestException as e:
                if self.logger:
                    self.logger.error(f"Failed to get DevDocs content: {e}")
                return json.dumps({"error": f"Failed to get content from DevDocs: {e}"})
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in get_devdocs_content: {e}")
                return json.dumps({"error": str(e)})

        @mcp_server.tool()
        async def list_devdocs_available() -> str:
            """List all available documentation sets in DevDocs"""
            try:
                docs_url = f"{self.devdocs_url}/docs.json"
                response = requests.get(docs_url, timeout=30)
                response.raise_for_status()
                return json.dumps(response.json(), indent=2)
            except requests.exceptions.RequestException as e:
                if self.logger:
                    self.logger.error(f"Failed to list DevDocs: {e}")
                return json.dumps({"error": f"Failed to connect to DevDocs: {e}"})
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in list_devdocs_available: {e}")
                return json.dumps({"error": str(e)})

        @mcp_server.tool()
        async def get_quick_reference(language: str, topic: str = None) -> str:
            """Get a quick reference for a programming language or specific topic"""
            try:
                if language not in self.supported_languages:
                    return json.dumps({"error": f"Language '{language}' not supported."})

                lang_config = self.supported_languages[language]
                quick_refs = self._load_quick_reference()

                if language not in quick_refs:
                    return json.dumps({"error": f"Quick reference not available for {language}."})

                ref_data = quick_refs[language]
                if topic and topic not in ref_data:
                    return json.dumps({"error": f"Topic '{topic}' not available for {language}."})

                response_data = {
                    "language": language,
                    "version": lang_config.get("version", "N/A"),
                }
                if topic:
                    response_data["topic"] = topic
                    response_data["reference"] = ref_data[topic]
                else:
                    response_data["quick_reference"] = ref_data
                    response_data["available_topics"] = list(ref_data.keys())

                return json.dumps(response_data, indent=2)

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in get_quick_reference: {e}")
                return json.dumps({"error": str(e)})

        @mcp_server.tool()
        async def download_docs_from_git(language: str, repo_url: str) -> str:
            """Download documentation from a Git repository"""
            if language not in self.supported_languages:
                return json.dumps({"error": f"Language '{language}' not supported."})

            config = self.supported_languages[language]
            lang_docs_dir = self.docs_dir / config["folder"]

            if lang_docs_dir.exists() and any(lang_docs_dir.iterdir()):
                return json.dumps({"error": f"Documentation for '{language}' already exists."})

            lang_docs_dir.mkdir(exist_ok=True)

            try:
                import subprocess
                result = subprocess.run(
                    ["git", "clone", "--depth", "1", repo_url, str(lang_docs_dir)],
                    capture_output=True, text=True, timeout=300, check=True
                )
                return json.dumps({
                    "success": True,
                    "message": f"Successfully cloned docs for {language}."
                })
            except subprocess.CalledProcessError as e:
                if self.logger:
                    self.logger.error(f"Git clone failed for {repo_url}: {e.stderr}")
                return json.dumps({"error": f"Git clone failed: {e.stderr}"})
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error downloading docs: {e}")
                return json.dumps({"error": str(e)})

    def _load_quick_reference(self) -> Dict[str, Any]:
        """Load quick reference data from JSON config file"""
        try:
            config_path = Path(__file__).parent.parent / "quick_reference.json"
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            if self.logger:
                self.logger.error(f"Error loading quick reference config: {e}")
            return {}

    def register_resources(self, mcp_server):
        """Register MCP resources for documentation access"""

        @mcp_server.resource("documentation://languages")
        async def list_documentation_languages() -> str:
            """List all supported programming languages for documentation"""
            try:
                languages_info = [
                    {
                        "language": lang,
                        "version": config.get("version", "Unknown"),
                        "folder": config["folder"],
                        "base_url": config.get("base_url", ""),
                        "devdocs_slug": config.get("devdocs_slug", ""),
                        "local_docs_available": (self.docs_dir / config["folder"]).exists()
                    }
                    for lang, config in self.supported_languages.items()
                ]
                return json.dumps(languages_info, indent=2)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error listing doc languages: {e}")
                return json.dumps({"error": str(e)})

        @mcp_server.resource("documentation://files/{language}")
        async def list_documentation_files(language: str) -> str:
            """List available documentation files for a specific language"""
            try:
                if language not in self.supported_languages:
                    return json.dumps({"error": f"Language '{language}' not supported."})

                config = self.supported_languages[language]
                lang_docs_dir = self.docs_dir / config["folder"]

                if not lang_docs_dir.exists():
                    return json.dumps([])

                files_info = [
                    {
                        "name": item.name,
                        "path": str(item.relative_to(lang_docs_dir)),
                        "size": item.stat().st_size,
                    }
                    for item in lang_docs_dir.rglob("*") if item.is_file()
                ]
                return json.dumps(files_info, indent=2)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error listing doc files for {language}: {e}")
                return json.dumps({"error": str(e)})

        @mcp_server.resource("documentation://content/{language}/{file_path}")
        async def get_documentation_file(language: str, file_path: str) -> str:
            """Get the content of a specific documentation file"""
            try:
                if language not in self.supported_languages:
                    return json.dumps({"error": f"Language '{language}' not supported."})

                config = self.supported_languages[language]
                lang_docs_dir = self.docs_dir / config["folder"]
                full_file_path = (lang_docs_dir / file_path).resolve()

                if not full_file_path.is_relative_to(lang_docs_dir.resolve()):
                    return json.dumps({"error": "Invalid file path."})

                if not full_file_path.exists():
                    return json.dumps({"error": "File not found."})

                content = full_file_path.read_text(encoding="utf-8", errors="replace")
                return json.dumps({"content": content})
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error reading doc file {file_path}: {e}")
                return json.dumps({"error": str(e)})
