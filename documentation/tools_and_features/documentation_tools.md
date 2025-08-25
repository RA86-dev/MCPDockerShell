# Documentation Tools

The Documentation Tools module provides access to over 700 programming language and framework documentation sources through DevDocs integration. This enables instant access to comprehensive documentation, code examples, and reference materials.

## Overview

The documentation system supports multiple programming languages and provides both local caching and remote access to ensure fast, reliable documentation lookup.

## Supported Languages

The system supports documentation for the following programming languages:

- **Python** (3.11) - Complete Python standard library and language reference
- **JavaScript** (ES2023) - Modern JavaScript features and Web APIs
- **Java** (OpenJDK 17) - Java SE documentation and APIs
- **C#** (.NET 7) - .NET and C# language documentation
- **Go** (1.21) - Go standard library and language specification
- **Rust** - Rust standard library and language guide
- **TypeScript** - TypeScript language reference
- **Node.js** - Node.js APIs and modules
- **React** - React library documentation
- **Vue.js** - Vue.js framework documentation
- **And 690+ more frameworks and libraries

## Core Functions

### Language Support Management

#### `list_supported_languages`
Get a list of all supported programming languages for documentation.

**Returns:** List of available programming languages

#### `get_language_doc_info`
Get information about downloaded documentation for a specific language.

**Parameters:**
- `language` (required): Programming language name (e.g., "python", "javascript")

**Returns:** Documentation information including version, status, and file count

#### `download_language_docs`
Download documentation for a specific programming language.

**Parameters:**
- `language` (required): Programming language to download documentation for

**Example:**
```python
# Download Python documentation
await download_language_docs(language="python")

# Check what's available
info = await get_language_doc_info(language="python")
```

### Documentation Search and Retrieval

#### `search_language_docs`
Search through documentation for a specific programming language.

**Parameters:**
- `language` (required): Programming language to search
- `query` (required): Search query
- `max_results` (optional): Maximum number of results to return (default: 10)

**Returns:** List of matching documentation entries with titles, content previews, and URLs

**Example:**
```python
# Search Python documentation for async/await
results = await search_language_docs(
    language="python",
    query="async await coroutines",
    max_results=5
)
```

#### `read_language_doc`
Read a specific documentation file for a programming language.

**Parameters:**
- `language` (required): Programming language
- `file_path` (required): Path to the specific documentation file
- `max_lines` (optional): Maximum number of lines to return (default: 500)

**Returns:** Documentation file content

#### `list_language_docs`
List available documentation files for a specific programming language.

**Parameters:**
- `language` (required): Programming language to list documentation for

**Returns:** List of available documentation file paths

### Python-Specific Functions (Legacy)

These functions provide backward compatibility for Python documentation:

#### `list_python_docs`
List available Python documentation files.

#### `read_python_doc`
Read a specific Python documentation file.

**Parameters:**
- `file_path` (required): Path to the Python documentation file
- `max_lines` (optional): Maximum number of lines to return (default: 500)

#### `search_python_docs`
Search through Python documentation.

**Parameters:**
- `query` (required): Search query
- `max_results` (optional): Maximum number of results (default: 10)

#### `get_python_doc_info`
Get information about Python documentation.

## DevDocs Integration

The system integrates with DevDocs (running on localhost:9292 by default) to provide:

- Real-time documentation access
- Comprehensive search capabilities
- Multi-language support
- Standardized documentation format
- Regular updates and synchronization

## Documentation Categories

### Programming Languages
- Core language syntax and semantics
- Standard library documentation
- Language-specific best practices
- Migration guides and changelogs

### Frameworks and Libraries
- Web frameworks (React, Vue, Angular, Django, Flask, etc.)
- Testing frameworks (Jest, PyTest, JUnit, etc.)
- Database libraries (SQLAlchemy, Mongoose, etc.)
- Utility libraries (Lodash, NumPy, etc.)

### Tools and Technologies
- Build tools (Webpack, Vite, Gradle, etc.)
- Package managers (npm, pip, Maven, etc.)
- Development tools (ESLint, Prettier, Black, etc.)
- Infrastructure tools (Docker, Kubernetes, etc.)

## Search Strategies

### Keyword Search
Search for specific terms, functions, or concepts:
```python
await search_language_docs("python", "list comprehension")
await search_language_docs("javascript", "async/await")
await search_language_docs("java", "stream API")
```

### Code Example Search
Find code examples and usage patterns:
```python
await search_language_docs("python", "decorator example")
await search_language_docs("react", "useEffect hook example")
```

### API Reference Search
Look up specific APIs and methods:
```python
await search_language_docs("python", "requests.get method")
await search_language_docs("javascript", "Array.prototype.map")
```

## Example Workflows

### Multi-Language Documentation Lookup
```python
# Compare similar concepts across languages
languages = ["python", "javascript", "java"]
query = "dictionary hash map"

for lang in languages:
    results = await search_language_docs(
        language=lang,
        query=query,
        max_results=3
    )
    print(f"Results for {lang}: {len(results)} found")
```

### Comprehensive Documentation Research
```python
# Research a complex topic thoroughly
topic = "async programming"
results = await search_language_docs("python", topic)

for result in results:
    # Read full documentation for detailed understanding
    full_doc = await read_language_doc(
        language="python",
        file_path=result['file_path']
    )
    # Process and analyze the documentation
```

### Framework Comparison
```python
# Compare React and Vue.js documentation
react_results = await search_language_docs("react", "component lifecycle")
vue_results = await search_language_docs("vue", "component lifecycle")

# Analyze differences in approach and implementation
```

## Best Practices

### Search Optimization
1. **Use Specific Terms**: Use precise technical terms for better results
2. **Include Context**: Add context like "example", "tutorial", or "reference"
3. **Try Variations**: Search for both formal terms and common aliases
4. **Filter Results**: Use max_results parameter to focus on most relevant matches

### Documentation Reading
1. **Check Versions**: Ensure documentation matches your target language version
2. **Read Completely**: Use read_language_doc for comprehensive understanding
3. **Cross-Reference**: Compare information across multiple sources
4. **Verify Examples**: Test code examples in your development environment

### Caching and Performance
1. **Download Locally**: Use download_language_docs for frequently used languages
2. **Monitor Status**: Check get_language_doc_info for download status
3. **Batch Queries**: Group related searches to minimize API calls
4. **Cache Results**: Store frequently accessed documentation locally

## Integration with Development Workflow

### Code Analysis
```python
# Analyze code and find relevant documentation
code_snippet = "async def process_data():"
# Search for async function documentation
docs = await search_language_docs("python", "async def function")
```

### Learning and Training
```python
# Create learning paths for new technologies
learning_topics = ["basics", "advanced", "best practices"]
for topic in learning_topics:
    results = await search_language_docs("react", topic)
    # Process results for training materials
```

### Code Review Support
```python
# Support code reviews with documentation lookup
function_name = "useCallback"
docs = await search_language_docs("react", f"{function_name} hook")
# Use documentation to validate code review comments
```

## Error Handling

The documentation tools include robust error handling for:
- Network connectivity issues
- Missing documentation files
- Invalid language specifications
- Search query processing errors
- File read/write permissions

Always check return values and implement appropriate fallbacks for production use.

## Performance Considerations

- Documentation search is optimized for speed with local caching
- Large documentation files are paginated with max_lines parameter
- DevDocs integration provides efficient search indexing
- Multiple concurrent searches are supported
- Memory usage is optimized through streaming and pagination