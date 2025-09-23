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

        # Supported languages and their documentation configurations
        self.supported_languages = {
            "python": {
                "folder": "python_docs",
                "version": "3.11",
                "base_url": "https://docs.python.org/3/",
                "devdocs_slug": "python~3.11",
            },
            "javascript": {
                "folder": "javascript_docs",
                "version": "ES2023",
                "base_url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript",
                "devdocs_slug": "javascript",
            },
            "java": {
                "folder": "java_docs",
                "version": "17",
                "base_url": "https://docs.oracle.com/en/java/javase/17/",
                "devdocs_slug": "openjdk~17",
            },
            "csharp": {
                "folder": "csharp_docs",
                "version": ".NET 7",
                "base_url": "https://docs.microsoft.com/en-us/dotnet/csharp/",
                "devdocs_slug": "dotnet~7",
            },
            "golang": {
                "folder": "go_docs",
                "version": "1.21",
                "base_url": "https://golang.org/doc/",
                "devdocs_slug": "go",
            },
            "rust": {
                "folder": "rust_docs",
                "version": "1.70",
                "base_url": "https://doc.rust-lang.org/",
                "devdocs_slug": "rust",
            },
            "cpp": {
                "folder": "cpp_docs",
                "version": "C++20",
                "base_url": "https://en.cppreference.com/w/cpp",
                "devdocs_slug": "cpp",
            },
            "php": {
                "folder": "php_docs",
                "version": "8.2",
                "base_url": "https://www.php.net/manual/en/",
                "devdocs_slug": "php~8.2",
            },
        }

    def register_tools(self, mcp_server):
        """Register documentation tools with the MCP server"""

        @mcp_server.tool()
        async def search_devdocs(
            query: str, language: str = None, max_results: int = 10
        ) -> str:
            """Search through DevDocs documentation"""
            try:
                # Build search URL
                search_url = f"{self.devdocs_url}/search"
                params = {"q": query, "limit": max_results}

                if language and language in self.supported_languages:
                    params["docs"] = self.supported_languages[language]["devdocs_slug"]

                response = requests.get(search_url, params=params, timeout=30)

                if response.status_code == 200:
                    return response.text

            except requests.exceptions.ConnectionError:
                return f"Cannot connect to DevDocs at {self.devdocs_url}. Is the service running?"
            except Exception as e:
                return f"Error searching DevDocs: {str(e)}"

        @mcp_server.tool()
        async def get_devdocs_content(path: str, language: str = None) -> str:
            """Get the full content of a specific documentation page from DevDocs"""
            try:
                # Construct the full URL
                if language and language in self.supported_languages:
                    doc_slug = self.supported_languages[language]["devdocs_slug"]
                    content_url = (
                        f"{self.devdocs_url}/docs/{doc_slug}/{path.lstrip('/')}"
                    )
                else:
                    content_url = f"{self.devdocs_url}/docs/{path.lstrip('/')}"

                response = requests.get(content_url, timeout=30)

                if response.status_code == 200:
                    try:
                        content_data = response.text
                        return content_data
                    except json.JSONDecodeError:
                        # Return raw text if JSON parsing fails
                        return response.text[:5000] + (
                            "..." if len(response.text) > 5000 else ""
                        )
                else:
                    return f"Failed to get content from {content_url}. Status: {response.status_code}"

            except requests.exceptions.ConnectionError:
                return f"Cannot connect to DevDocs at {self.devdocs_url}"
            except Exception as e:
                return f"Error getting DevDocs content: {str(e)}"

        @mcp_server.tool()
        async def list_devdocs_available() -> str:
            """List all available documentation sets in DevDocs"""
            try:
                docs_url = f"{self.devdocs_url}/docs.json"
                response = requests.get(docs_url, timeout=30)

                if response.status_code == 200:
                    docs_list = response.json()

                    # Filter and organize the results
                    popular_docs = []
                    all_docs = []

                    for doc in docs_list:
                        doc_info = {
                            "name": doc.get("name", ""),
                            "slug": doc.get("slug", ""),
                            "version": doc.get("version", ""),
                            "description": doc.get("attribution", ""),
                        }
                        all_docs.append(doc_info)

                        # Mark popular/supported languages
                        slug = doc.get("slug", "").lower()
                        for lang_key in self.supported_languages:
                            if lang_key in slug or slug.startswith(lang_key):
                                popular_docs.append(doc_info)
                                break

                    return json.dumps(
                        {
                            "total_available": len(all_docs),
                            "popular_languages": popular_docs[:20],  # Top 20 popular
                            "all_available": all_docs[
                                :50
                            ],  # First 50 to avoid overwhelming
                            "devdocs_url": self.devdocs_url,
                        },
                        indent=2,
                    )
                else:
                    return f"Failed to get docs list. Status: {response.status_code}"

            except requests.exceptions.ConnectionError:
                return f"Cannot connect to DevDocs at {self.devdocs_url}"
            except Exception as e:
                return f"Error listing DevDocs: {str(e)}"

        @mcp_server.tool()
        async def get_quick_reference(language: str, topic: str = None) -> str:
            """Get a quick reference for a programming language or specific topic"""
            try:
                if language not in self.supported_languages:
                    return f"Language '{language}' not supported. Available: {', '.join(self.supported_languages.keys())}"

                lang_config = self.supported_languages[language]

                # Create quick reference based on language
                quick_refs = {
                    "python": {
                        "syntax": {
                            "variables": "name = value",
                            "functions": "def function_name(param):\n    return value",
                            "classes": "class ClassName:\n    def __init__(self):\n        pass",
                            "loops": "for item in iterable:\n    pass\n\nwhile condition:\n    pass",
                            "conditions": "if condition:\n    pass\nelif other_condition:\n    pass\nelse:\n    pass",
                        },
                        "data_types": [
                            "int",
                            "float",
                            "str",
                            "list",
                            "dict",
                            "tuple",
                            "set",
                            "bool",
                        ],
                        "common_imports": [
                            "import os",
                            "import sys",
                            "import json",
                            "import requests",
                            "from pathlib import Path",
                        ],
                        "useful_functions": [
                            "len()",
                            "range()",
                            "enumerate()",
                            "zip()",
                            "map()",
                            "filter()",
                        ],
                    },
                    "javascript": {
                        "syntax": {
                            "variables": "const name = value; let mutable = value; var old = value;",
                            "functions": "function name(param) { return value; }\n// or\nconst name = (param) => value;",
                            "objects": "const obj = { key: value, method() { return this.key; } };",
                            "loops": "for (let i = 0; i < arr.length; i++) {}\nfor (const item of arr) {}\nfor (const key in obj) {}",
                            "conditions": "if (condition) {\n} else if (other) {\n} else {\n}",
                        },
                        "data_types": [
                            "number",
                            "string",
                            "boolean",
                            "object",
                            "array",
                            "null",
                            "undefined",
                        ],
                        "common_methods": [
                            "array.map()",
                            "array.filter()",
                            "array.reduce()",
                            "string.split()",
                            "JSON.parse()",
                        ],
                        "es6_features": [
                            "const/let",
                            "arrow functions",
                            "destructuring",
                            "template literals",
                            "modules",
                        ],
                    },
                }

                if language in quick_refs:
                    ref_data = quick_refs[language]

                    if topic and topic in ref_data:
                        return json.dumps(
                            {
                                "language": language,
                                "topic": topic,
                                "reference": ref_data[topic],
                                "version": lang_config["version"],
                            },
                            indent=2,
                        )
                    else:
                        return json.dumps(
                            {
                                "language": language,
                                "version": lang_config["version"],
                                "quick_reference": ref_data,
                                "available_topics": (
                                    list(ref_data.keys())
                                    if isinstance(ref_data, dict)
                                    else []
                                ),
                            },
                            indent=2,
                        )
                else:
                    # Generic response for unsupported languages
                    return json.dumps(
                        {
                            "language": language,
                            "version": lang_config["version"],
                            "message": f"Quick reference not yet available for {language}",
                            "documentation_url": lang_config["base_url"],
                            "devdocs_slug": lang_config["devdocs_slug"],
                        },
                        indent=2,
                    )

            except Exception as e:
                return f"Error getting quick reference: {str(e)}"

    def register_resources(self, mcp_server):
        """Register MCP resources for documentation access"""

        @mcp_server.resource("documentation://languages")
        async def list_documentation_languages() -> str:
            """List all supported programming languages for documentation"""
            try:
                languages_info = []
                for lang, config in self.supported_languages.items():
                    lang_docs_dir = self.docs_dir / config["folder"]
                    languages_info.append(
                        {
                            "language": lang,
                            "version": config.get("version", "Unknown"),
                            "folder": config["folder"],
                            "base_url": config.get("base_url", ""),
                            "devdocs_slug": config.get("devdocs_slug", ""),
                            "local_docs_available": (
                                lang_docs_dir.exists() and any(lang_docs_dir.iterdir())
                                if lang_docs_dir.exists()
                                else False
                            ),
                        }
                    )

                return json.dumps(
                    {
                        "supported_languages": languages_info,
                        "total_count": len(languages_info),
                        "docs_directory": str(self.docs_dir),
                        "devdocs_url": self.devdocs_url,
                    },
                    indent=2,
                )

            except Exception as e:
                return f"Error listing documentation languages: {str(e)}"

        @mcp_server.resource("documentation://files/{language}")
        async def list_documentation_files(language: str) -> str:
            """List available documentation files for a specific language"""
            try:
                if language not in self.supported_languages:
                    return f"Language '{language}' not supported"

                config = self.supported_languages[language]
                lang_docs_dir = self.docs_dir / config["folder"]

                if not lang_docs_dir.exists():
                    return json.dumps(
                        {
                            "language": language,
                            "files": [],
                            "message": f"No local documentation found for {language}",
                            "suggestion": f"Use search_devdocs to search online documentation",
                        },
                        indent=2,
                    )

                files_info = []
                for file_path in lang_docs_dir.rglob("*.txt"):
                    try:
                        stat = file_path.stat()
                        files_info.append(
                            {
                                "name": file_path.name,
                                "path": str(file_path.relative_to(lang_docs_dir)),
                                "size": stat.st_size,
                                "modified": stat.st_mtime,
                            }
                        )
                    except Exception:
                        continue

                return json.dumps(
                    {
                        "language": language,
                        "files": files_info,
                        "total_files": len(files_info),
                        "docs_directory": str(lang_docs_dir),
                    },
                    indent=2,
                )

            except Exception as e:
                return f"Error listing documentation files: {str(e)}"

        @mcp_server.resource("documentation://content/{language}/{file_path}")
        async def get_documentation_file(language: str, file_path: str) -> str:
            """Get the content of a specific documentation file"""
            try:
                if language not in self.supported_languages:
                    return f"Language '{language}' not supported"

                config = self.supported_languages[language]
                lang_docs_dir = self.docs_dir / config["folder"]

                full_file_path = lang_docs_dir / file_path

                if not full_file_path.exists():
                    return f"Documentation file not found: {file_path}"

                # Security check - ensure file is within docs directory
                if not str(full_file_path.resolve()).startswith(
                    str(lang_docs_dir.resolve())
                ):
                    return "Error: Invalid file path"

                with open(full_file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                return json.dumps(
                    {
                        "language": language,
                        "file_path": file_path,
                        "content": content[:10000]
                        + ("..." if len(content) > 10000 else ""),  # Limit content size
                        "size": len(content),
                        "truncated": len(content) > 10000,
                    },
                    indent=2,
                )

            except Exception as e:
                return f"Error reading documentation file: {str(e)}"
