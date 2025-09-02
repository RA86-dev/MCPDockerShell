# Firecrawl Tools

The Firecrawl Tools module provides web scraping and crawling capabilities using the Firecrawl service. This allows you to scrape websites, extract data, and perform web searches.

## Configuration

To use the Firecrawl tools, you need to enable them by setting the `ENABLE_FIRECRAWL` environment variable to `true`. You can use either a local Firecrawl instance or the cloud-based service with an API key.

- **Local Instance:** Set `ENABLE_LOCAL_FIRECRAWL` to `true` and provide the URL of your local Firecrawl instance in the `LOCAL_URL` environment variable.
- **Cloud Service:** Provide your Firecrawl API key in the `FIRECRAWL_API_KEY` environment variable.

If no API key is provided, the server will default to using a local Firecrawl instance at `http://localhost:3002`.

## Core Tools

### `scrape_url`
Scrapes a single URL and returns the content.

**Parameters:**
- `url` (required): The URL to scrape.
- `include_html` (optional): Whether to include the raw HTML in the response (default: `False`).
- `include_metadata` (optional): Whether to include metadata (e.g., title, description) in the response (default: `True`).

**Returns:** A JSON string with the scraped content, and optionally the HTML and metadata.

**Example:**
```python
# Scrape a blog post
scrape_result = await scrape_url(
    url="https://example.com/blog/my-post"
)
```

### `crawl_url`
Crawls a website starting from a given URL and returns the content of all crawled pages.

**Parameters:**
- `url` (required): The starting URL to crawl.
- `max_depth` (optional): The maximum depth to crawl (default: 2).
- `max_pages` (optional): The maximum number of pages to crawl (default: 10).
- `include_html` (optional): Whether to include the raw HTML in the response (default: `False`).

**Returns:** A JSON string with a list of scraped pages.

**Example:**
```python
# Crawl a documentation website
crawl_result = await crawl_url(
    url="https://docs.example.com",
    max_depth=3,
    max_pages=20
)
```

### `search`
Performs a web search using the Firecrawl search service.

**Parameters:**
- `query` (required): The search query.
- `max_results` (optional): The maximum number of search results to return (default: 10).

**Returns:** A JSON string with a list of search results.

**Example:**
```python
# Search for information about a topic
search_result = await search(
    query="What is the latest version of Python?",
    max_results=5
)
```
