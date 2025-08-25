# API Reference

This comprehensive API reference documents all available functions and tools in the MCP Docker Developer Server.

## Table of Contents

- [Docker Management API](#docker-management-api)
- [Browser Automation API](#browser-automation-api)
- [Documentation API](#documentation-api)
- [Development Tools API](#development-tools-api)
- [Monitoring API](#monitoring-api)
- [Workflow API](#workflow-api)
- [System Information API](#system-information-api)
- [Error Handling](#error-handling)

## Docker Management API

### Container Lifecycle

#### `create_container(image, name=None, command=None, environment=None, ports=None, use_gpu=False)`

Creates and starts a new Docker container.

**Parameters:**
- `image` (str, required): Docker image name
- `name` (str, optional): Container name
- `command` (str, optional): Command to run in container
- `environment` (dict, optional): Environment variables
- `ports` (dict, optional): Port mappings {container_port: host_port}
- `use_gpu` (bool, optional): Enable GPU access

**Returns:**
```python
{
    "id": "container_id",
    "name": "container_name",
    "image": "image_name",
    "status": "running",
    "ports": {"5000": 8080}
}
```

**Example:**
```python
container = await create_container(
    image="python:3.11-slim",
    name="python-dev",
    environment={"PYTHONPATH": "/workspace"},
    ports={"5000": 8080}
)
```

#### `list_containers()`

Lists all active containers managed by the MCP server.

**Returns:**
```python
[
    {
        "id": "container_id",
        "name": "container_name", 
        "image": "image_name",
        "status": "running",
        "created": "2024-01-01T12:00:00Z"
    }
]
```

#### `start_container(container_id)`, `stop_container(container_id)`, `restart_container(container_id)`

Control container lifecycle states.

**Parameters:**
- `container_id` (str, required): Container ID

**Returns:**
```python
{
    "success": true,
    "message": "Container started successfully",
    "container_id": "container_id"
}
```

#### `delete_container(container_id)`

Stops and removes a container completely.

**Parameters:**
- `container_id` (str, required): Container ID

**Returns:**
```python
{
    "success": true,
    "message": "Container deleted successfully"
}
```

### Command Execution

#### `execute_command(container_id, command)`

Execute a command inside a running container.

**Parameters:**
- `container_id` (str, required): Target container ID
- `command` (str, required): Command to execute

**Returns:**
```python
{
    "success": true,
    "stdout": "command output",
    "stderr": "error output",
    "exit_code": 0,
    "execution_time": 1.23
}
```

#### `stream_command_execution(container_id, command)`

Execute a command and stream the output in real-time.

**Parameters:**
- `container_id` (str, required): Target container ID
- `command` (str, required): Command to execute

**Returns:**
```python
{
    "stream_key": "stream_id",
    "status": "started"
}
```

### File Operations

#### `create_file_in_container(container_id, file_path, content)`

Create a file with specified content inside a container.

**Parameters:**
- `container_id` (str, required): Target container ID
- `file_path` (str, required): File path in container
- `content` (str, required): File content

**Returns:**
```python
{
    "success": true,
    "message": "File created successfully",
    "file_path": "/workspace/file.py"
}
```

#### `read_file_in_container(container_id, file_path)`

Read the contents of a file inside a container.

**Parameters:**
- `container_id` (str, required): Target container ID
- `file_path` (str, required): File path to read

**Returns:**
```python
{
    "success": true,
    "content": "file contents",
    "size": 1024,
    "modified": "2024-01-01T12:00:00Z"
}
```

#### `write_file_in_container(container_id, file_path, content, append=False)`

Write content to a file inside a container.

**Parameters:**
- `container_id` (str, required): Target container ID
- `file_path` (str, required): Target file path
- `content` (str, required): Content to write
- `append` (bool, optional): Append to existing file

#### `delete_file_in_container(container_id, file_path)`

Delete a file inside a container.

**Parameters:**
- `container_id` (str, required): Target container ID
- `file_path` (str, required): File path to delete

#### `list_files_in_container(container_id, directory_path="/workspace")`

List files and directories in a container directory.

**Parameters:**
- `container_id` (str, required): Target container ID
- `directory_path` (str, optional): Directory path

**Returns:**
```python
{
    "files": [
        {
            "name": "file.py",
            "type": "file",
            "size": 1024,
            "modified": "2024-01-01T12:00:00Z",
            "permissions": "rw-r--r--"
        },
        {
            "name": "subdirectory",
            "type": "directory",
            "size": 4096,
            "modified": "2024-01-01T12:00:00Z"
        }
    ],
    "total_files": 15,
    "total_size": 10485760
}
```

## Browser Automation API

### Playwright API

#### `playwright_launch_browser(browser_type="chromium", headless=True, args=None)`

Launch a Playwright browser instance.

**Parameters:**
- `browser_type` (str, optional): "chromium", "firefox", or "webkit"
- `headless` (bool, optional): Run in headless mode
- `args` (list, optional): Additional browser arguments

**Returns:**
```python
{
    "browser_id": "browser_uuid",
    "browser_type": "chromium",
    "headless": true
}
```

#### `playwright_create_page(browser_id, viewport_width=1920, viewport_height=1080)`

Create a new page in a browser.

**Parameters:**
- `browser_id` (str, required): Browser ID
- `viewport_width` (int, optional): Page width
- `viewport_height` (int, optional): Page height

**Returns:**
```python
{
    "page_id": "page_uuid",
    "browser_id": "browser_uuid",
    "viewport": {"width": 1920, "height": 1080}
}
```

#### `playwright_navigate(page_id, url, wait_until="load")`

Navigate to a URL.

**Parameters:**
- `page_id` (str, required): Page ID
- `url` (str, required): URL to navigate to
- `wait_until` (str, optional): "load", "domcontentloaded", "networkidle"

**Returns:**
```python
{
    "success": true,
    "url": "https://example.com",
    "title": "Page Title",
    "load_time": 1.23
}
```

#### `playwright_click(page_id, selector, timeout=30000)`

Click an element on the page.

**Parameters:**
- `page_id` (str, required): Page ID
- `selector` (str, required): CSS selector
- `timeout` (int, optional): Timeout in milliseconds

#### `playwright_type(page_id, selector, text, timeout=30000)`

Type text into an element.

**Parameters:**
- `page_id` (str, required): Page ID
- `selector` (str, required): CSS selector
- `text` (str, required): Text to type
- `timeout` (int, optional): Timeout in milliseconds

#### `playwright_screenshot(page_id, filename=None, full_page=False, return_base64=False)`

Take a screenshot.

**Parameters:**
- `page_id` (str, required): Page ID
- `filename` (str, optional): Screenshot filename
- `full_page` (bool, optional): Capture full page
- `return_base64` (bool, optional): Return as base64

**Returns:**
```python
{
    "success": true,
    "filename": "screenshot.png",
    "size": {"width": 1920, "height": 1080},
    "base64": "base64_data"  # if return_base64=True
}
```

### Selenium API

#### `selenium_launch_driver(browser_type="chrome", headless=True, options=None)`

Launch a Selenium WebDriver.

**Parameters:**
- `browser_type` (str, optional): "chrome" or "firefox"
- `headless` (bool, optional): Run in headless mode
- `options` (list, optional): Browser options

**Returns:**
```python
{
    "driver_id": "driver_uuid",
    "browser_type": "chrome",
    "headless": true
}
```

## Documentation API

### Language Documentation

#### `list_supported_languages()`

Get list of supported programming languages.

**Returns:**
```python
[
    "python",
    "javascript", 
    "java",
    "go",
    "rust",
    "csharp"
]
```

#### `search_language_docs(language, query, max_results=10)`

Search documentation for a specific language.

**Parameters:**
- `language` (str, required): Programming language
- `query` (str, required): Search query
- `max_results` (int, optional): Maximum results

**Returns:**
```python
[
    {
        "title": "Async Programming",
        "summary": "Guide to async/await in Python",
        "url": "https://docs.python.org/3/library/asyncio.html",
        "file_path": "python/library/asyncio.html",
        "relevance_score": 0.95
    }
]
```

#### `read_language_doc(language, file_path, max_lines=500)`

Read specific documentation file.

**Parameters:**
- `language` (str, required): Programming language
- `file_path` (str, required): Documentation file path
- `max_lines` (int, optional): Maximum lines to return

**Returns:**
```python
{
    "content": "documentation content",
    "language": "python",
    "file_path": "python/library/asyncio.html",
    "lines": 450,
    "last_modified": "2024-01-01T12:00:00Z"
}
```

#### `download_language_docs(language)`

Download documentation for a specific language.

**Parameters:**
- `language` (str, required): Programming language to download

**Returns:**
```python
{
    "success": true,
    "language": "python",
    "download_status": "completed",
    "files_downloaded": 1250,
    "total_size": "150MB"
}
```

## Monitoring API

### Container Metrics

#### `get_container_metrics(container_id, time_range="5m")`

Get resource metrics for a container.

**Parameters:**
- `container_id` (str, required): Container ID
- `time_range` (str, optional): Time range for metrics

**Returns:**
```python
{
    "container_id": "container_id",
    "timestamp": "2024-01-01T12:00:00Z",
    "cpu_percent": 45.2,
    "memory_usage": "512MB",
    "memory_percent": 25.6,
    "disk_io": {
        "read": "10MB/s",
        "write": "5MB/s"
    },
    "network_io": {
        "rx": "1MB/s",
        "tx": "500KB/s"
    },
    "uptime": "2h 30m"
}
```

#### `get_system_metrics()`

Get host system metrics.

**Returns:**
```python
{
    "timestamp": "2024-01-01T12:00:00Z",
    "cpu_percent": 35.4,
    "memory_percent": 68.2,
    "disk_usage": {
        "total": "500GB",
        "used": "250GB",
        "available": "250GB",
        "percent": 50.0
    },
    "load_average": [1.2, 1.5, 1.8],
    "uptime": "5 days, 12:30:15"
}
```

### Health Checks

#### `check_system_health()`

Perform comprehensive system health check.

**Returns:**
```python
{
    "overall_status": "healthy",
    "timestamp": "2024-01-01T12:00:00Z",
    "components": {
        "docker_daemon": {
            "status": "healthy",
            "version": "24.0.0"
        },
        "containers": {
            "status": "healthy",
            "running": 5,
            "stopped": 2
        },
        "storage": {
            "status": "healthy",
            "available_space": "250GB"
        },
        "network": {
            "status": "healthy",
            "connectivity": "good"
        }
    }
}
```

## Workflow API

### Workflow Management

#### `create_workflow(workflow_config, name, description=None)`

Create a new workflow definition.

**Parameters:**
- `workflow_config` (dict, required): Workflow configuration
- `name` (str, required): Workflow name
- `description` (str, optional): Workflow description

**Returns:**
```python
{
    "workflow_id": "workflow_uuid",
    "name": "development_pipeline",
    "created": "2024-01-01T12:00:00Z",
    "tasks": 5
}
```

#### `execute_workflow(workflow_id, parameters=None, environment=None)`

Execute a workflow.

**Parameters:**
- `workflow_id` (str, required): Workflow ID
- `parameters` (dict, optional): Runtime parameters
- `environment` (dict, optional): Environment variables

**Returns:**
```python
{
    "execution_id": "execution_uuid",
    "workflow_id": "workflow_uuid",
    "status": "started",
    "started_at": "2024-01-01T12:00:00Z"
}
```

#### `get_workflow_status(execution_id)`

Get workflow execution status.

**Parameters:**
- `execution_id` (str, required): Execution ID

**Returns:**
```python
{
    "execution_id": "execution_uuid",
    "status": "running",
    "progress": 60,
    "current_task": "run_tests",
    "completed_tasks": 3,
    "total_tasks": 5,
    "started_at": "2024-01-01T12:00:00Z",
    "estimated_completion": "2024-01-01T12:15:00Z"
}
```

## System Information API

### GPU Support

#### `get_gpu_status()`

Get NVIDIA GPU status and availability.

**Returns:**
```python
{
    "gpu_available": true,
    "nvidia_driver": "525.60.11",
    "cuda_version": "12.0",
    "gpus": [
        {
            "id": 0,
            "name": "NVIDIA GeForce RTX 3080",
            "memory_total": "10GB",
            "memory_used": "2GB",
            "utilization": 45
        }
    ]
}
```

### Image Management

#### `list_allowed_images()`

List Docker images allowed for container creation.

**Returns:**
```python
[
    {
        "name": "python:3.11-slim",
        "category": "programming_language",
        "size": "125MB",
        "last_updated": "2024-01-01T12:00:00Z"
    },
    {
        "name": "node:18-alpine",
        "category": "programming_language", 
        "size": "110MB",
        "last_updated": "2024-01-01T12:00:00Z"
    }
]
```

### Workspace Management

#### `upload_file(filename, content)`

Upload a file to the shared workspace.

**Parameters:**
- `filename` (str, required): Filename
- `content` (str, required): File content

**Returns:**
```python
{
    "success": true,
    "filename": "uploaded_file.py",
    "size": 1024,
    "path": "/workspace/uploaded_file.py"
}
```

#### `list_workspace_files()`

List files in the shared workspace.

**Returns:**
```python
{
    "files": [
        {
            "name": "script.py",
            "size": 1024,
            "modified": "2024-01-01T12:00:00Z",
            "type": "file"
        }
    ],
    "total_files": 15,
    "total_size": "2MB"
}
```

## Error Handling

### Standard Error Response Format

All API functions return errors in a consistent format:

```python
{
    "success": false,
    "error": {
        "code": "CONTAINER_NOT_FOUND",
        "message": "Container with ID 'invalid_id' not found",
        "details": {
            "container_id": "invalid_id",
            "available_containers": ["container1", "container2"]
        },
        "timestamp": "2024-01-01T12:00:00Z"
    }
}
```

### Common Error Codes

#### Container Operations
- `CONTAINER_NOT_FOUND`: Container ID does not exist
- `CONTAINER_NOT_RUNNING`: Container is not in running state
- `IMAGE_NOT_ALLOWED`: Docker image is not in allowed list
- `INSUFFICIENT_RESOURCES`: Not enough system resources
- `PORT_ALREADY_IN_USE`: Requested port is already in use

#### File Operations
- `FILE_NOT_FOUND`: File does not exist in container
- `PERMISSION_DENIED`: Insufficient permissions for file operation
- `DISK_FULL`: Not enough disk space
- `INVALID_PATH`: Invalid file or directory path

#### Browser Automation
- `BROWSER_LAUNCH_FAILED`: Could not launch browser
- `PAGE_NOT_FOUND`: Page ID does not exist
- `ELEMENT_NOT_FOUND`: CSS selector did not match any elements
- `NAVIGATION_TIMEOUT`: Page navigation timed out

#### Documentation
- `LANGUAGE_NOT_SUPPORTED`: Programming language not supported
- `DOCS_NOT_AVAILABLE`: Documentation not downloaded or available
- `SEARCH_FAILED`: Documentation search failed

### Error Handling Best Practices

1. **Always check success field**: Before processing results, check if the operation succeeded
2. **Handle specific error codes**: Implement specific handling for different error types
3. **Use error details**: Extract useful information from error details for debugging
4. **Implement retries**: For transient errors, implement retry logic with exponential backoff
5. **Log errors appropriately**: Log errors with sufficient context for debugging

### Example Error Handling

```python
try:
    result = await create_container(image="python:3.11-slim")
    if result.get("success"):
        container_id = result["id"]
        # Process successful result
    else:
        error = result.get("error", {})
        if error.get("code") == "IMAGE_NOT_ALLOWED":
            # Handle image not allowed error
            print(f"Image not allowed: {error['message']}")
        else:
            # Handle other errors
            print(f"Container creation failed: {error['message']}")
except Exception as e:
    # Handle unexpected exceptions
    print(f"Unexpected error: {str(e)}")
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **Default limit**: 100 requests per minute per client
- **Burst limit**: Up to 10 requests per second
- **Container operations**: Additional limits based on system resources

### Rate Limit Headers

API responses include rate limit information:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1640995200
```

## Authentication

API access requires authentication via environment variables:

```bash
export MCP_SECRET_KEY="your-secret-key-here"
```

Authentication failures return error code `AUTHENTICATION_REQUIRED`.

This API reference provides comprehensive documentation for all available functions in the MCP Docker Developer Server. For implementation examples, see the [Usage Examples](../examples/usage_examples.md) documentation.