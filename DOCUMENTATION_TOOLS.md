# Multi-Language Documentation Tools

This MCPDocker server now includes comprehensive documentation support for multiple programming languages.

## Supported Languages

- **Python** (3.13) - Official Python documentation
- **C#** (net-7.0) - .NET documentation from GitHub
- **JavaScript** (latest) - MDN documentation from GitHub
- **Java** (17) - Oracle Java documentation (download not yet implemented)
- **Go** (latest) - Go documentation from GitHub
- **Rust** (latest) - Rust documentation from GitHub

## MCP Tools Available

### General Documentation Tools

1. **`list_supported_languages()`**
   - Lists all supported programming languages with their versions and availability status
   - Returns: List of strings with language info

2. **`download_language_docs(language: str)`**
   - Downloads documentation for a specific programming language
   - Parameters: language (python, csharp, javascript, java, go, rust)
   - Returns: Success/error message

### Language-Specific Tools

3. **`list_language_docs(language: str)`**
   - Lists available documentation files for a specific language
   - Parameters: language name
   - Returns: List of file paths

4. **`read_language_doc(language: str, file_path: str, max_lines: int = 500)`**
   - Reads content of a specific documentation file
   - Parameters: language, file path, optional line limit
   - Returns: File content (truncated if too long)

5. **`search_language_docs(language: str, query: str, max_results: int = 10)`**
   - Searches through documentation for specific content
   - Parameters: language, search query, max results
   - Returns: Formatted search results with context

6. **`get_language_doc_info(language: str)`**
   - Gets information about downloaded documentation for a language
   - Parameters: language name
   - Returns: Version, location, file count, size info

### Legacy Python-Specific Tools (maintained for compatibility)

7. **`list_python_docs()`** - Lists Python documentation files
8. **`read_python_doc(file_path: str, max_lines: int = 500)`** - Reads Python doc file
9. **`search_python_docs(query: str, max_results: int = 10)`** - Searches Python docs
10. **`get_python_doc_info()`** - Gets Python documentation info

## MCP Resources Available

### 1. Languages Overview
- **URI**: `documentation://languages`
- **Description**: Lists all supported languages with availability status
- **Returns**: JSON with language details

### 2. Language File Listing
- **URI**: `documentation://{language}/files`
- **Description**: Lists all documentation files for a specific language
- **Parameters**: language name
- **Returns**: JSON with file metadata

### 3. File Content Access
- **URI**: `documentation://{language}/file/{file_path}`
- **Description**: Gets content of a specific documentation file
- **Parameters**: language name, file path
- **Returns**: JSON with file content and metadata

## Directory Structure

```
documentation/
├── python-docs/          # Python 3.13 documentation
├── csharp-docs/          # C# .NET documentation
├── javascript-docs/      # JavaScript/MDN documentation
├── java-docs/            # Java documentation (when implemented)
├── go-docs/              # Go documentation
└── rust-docs/            # Rust documentation
```

## Usage Examples

### Using Tools
```python
# List supported languages
languages = await list_supported_languages()

# Download Python documentation
result = await download_language_docs("python")

# Search for "async" in Python docs
results = await search_language_docs("python", "async", 5)

# Read a specific file
content = await read_language_doc("python", "library/asyncio.txt", 100)

# Get documentation info
info = await get_language_doc_info("python")
```

### Using Resources
```python
# Access via MCP resource URIs
languages_list = await get_resource("documentation://languages")
python_files = await get_resource("documentation://python/files")
file_content = await get_resource("documentation://python/file/library/asyncio.txt")
```

## Features

- **Multi-format support**: .txt, .md, .rst files
- **Smart extraction**: Only extracts relevant documentation files
- **Search functionality**: Case-insensitive search with context
- **Version tracking**: Each language includes version information
- **Error handling**: Comprehensive error handling and user feedback
- **Resource efficiency**: Skip downloads if documentation already exists
- **Truncation support**: Large files are truncated with notification
- **Status monitoring**: Easy way to check availability

## Benefits

1. **Comprehensive Coverage**: Support for major programming languages
2. **Dual Access**: Both tools and resources for different use cases
3. **Search Capabilities**: Find relevant information quickly
4. **Structured Access**: Well-organized directory structure
5. **Efficient Storage**: Smart downloading and extraction
6. **Developer Friendly**: Easy-to-use APIs for AI assistants