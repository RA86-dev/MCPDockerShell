# Documentation Tools

The Documentation Tools module provides access to a vast collection of programming language and framework documentation through a locally hosted DevDocs instance.

## Core Tools

### `search_devdocs`
Search through the DevDocs documentation.

**Parameters:**
- `query` (required): The search term.
- `language` (optional): The language to search within (e.g., "python", "javascript"). If not provided, searches all documentation.
- `max_results` (optional): The maximum number of results to return (default: 10).

**Returns:** A JSON string containing the search results, including title, path, and a summary for each result.

**Example:**
```python
# Search for "async await" in Python documentation
results = await search_devdocs(
    query="async await",
    language="python",
    max_results=5
)
```

### `get_devdocs_content`
Get the full content of a specific documentation page from DevDocs.

**Parameters:**
- `path` (required): The path to the documentation page (e.g., "library/asyncio.html"). You can get this from the `search_devdocs` results.
- `language` (optional): The language of the documentation.

**Returns:** A JSON string with the page's content, title, and URL.

**Example:**
```python
# Get the content of the asyncio page
content = await get_devdocs_content(
    path="library/asyncio.html",
    language="python"
)
```

### `list_devdocs_available`
List all available documentation sets in the DevDocs instance.

**Returns:** A JSON string with a list of all available documentation, including popular languages and frameworks.

### `get_quick_reference`
Get a quick reference for a programming language. This provides a summary of common syntax, data types, and functions.

**Parameters:**
- `language` (required): The programming language (e.g., "python", "javascript").
- `topic` (optional): A specific topic to get a reference for (e.g., "syntax", "data_types").

**Returns:** A JSON string with the quick reference information. Note: This feature is still under development and only supports a limited number of languages and topics.

## Local Documentation Management

### `download_docs_from_git`
Download documentation for a specific language from a Git repository. This allows you to populate the local documentation directories for offline access.

**Parameters:**
- `language` (required): The programming language for which you are downloading the documentation. This must be one of the supported languages.
- `repo_url` (required): The URL of the Git repository containing the documentation.

**Returns:** A string confirming the successful download or an error message.

**Example:**
```python
# Download the Python documentation from its GitHub repository
await download_docs_from_git(
    language="python",
    repo_url="https://github.com/python/cpython.git"
)
```

## MCP Resources

The documentation tools also expose MCP resources for more direct access to documentation information.

### `documentation://languages`
Lists all the programming languages that are explicitly supported and configured in the server.

**Example:**
```
documentation://languages
```

### `documentation://files/{language}`
Lists the available *local* documentation files for a specific language.

**Note:** This feature is not fully implemented, as there is no mechanism to download and store documentation files locally. It will currently return an empty list.

**Example:**
```
documentation://files/python
```

### `documentation://content/{language}/{file_path}`
Gets the content of a specific *local* documentation file.

**Note:** Like the `files` resource, this is not fully functional yet.

## Example Workflow

```python
# 1. See what documentation is available
available_docs = await list_devdocs_available()
print(available_docs)

# 2. Search for information on Python's "requests" library
search_results = await search_devdocs(
    query="requests get",
    language="python"
)
print(search_results)

# 3. Get the full content of the first search result
# (Assuming the first result has a path like "requests/api/#requests.get")
import json
results_data = json.loads(search_results)
first_result_path = results_data["results"][0]["path"]

full_content = await get_devdocs_content(
    path=first_result_path,
    language="python"
)
print(full_content)

# 4. Get a quick reference for Python syntax
quick_ref = await get_quick_reference(
    language="python",
    topic="syntax"
)
print(quick_ref)
```
