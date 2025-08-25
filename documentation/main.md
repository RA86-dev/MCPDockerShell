# MCP Docker Developer Server Documentation

MCP Developer Server is a Python-based MCP (Model Context Protocol) server designed to supercharge your development workflow. It provides instant access to 700+ documentation sources and creates isolated Docker containers for safe code testing and experimentation.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Tools and Features](#tools-and-features)
5. [Usage Examples](#usage-examples)
6. [Troubleshooting](#troubleshooting)
7. [API Reference](#api-reference)

## Getting Started

The MCP Docker Developer Server combines two powerful capabilities:

### Documentation Access
- Access over 700 programming language and framework documentation sources
- Search across multiple documentation sources simultaneously
- Get summaries, examples, and detailed explanations
- Powered by DevDocs integration

### Containerized Development
- Create isolated Docker containers for safe code testing
- Support for multiple programming languages and frameworks
- Optional NVIDIA GPU acceleration for AI/ML workloads
- Browser automation tools for testing web applications

## Installation

See [Installation Guide](installation/install_docker.md) for detailed setup instructions.

## Configuration

The server uses a flexible configuration system that allows you to:
- Enable/disable specific tool categories
- Configure security levels
- Set resource limits
- Customize Docker container settings

For detailed configuration options, see [Configuration Guide](configuration/config_guide.md).

## Tools and Features

The MCP Docker Developer Server provides several tool categories:

### [Docker Tools](tools_and_features/docker_tools.md)
- Container management (create, start, stop, delete)
- File operations within containers
- Command execution
- Port streaming and networking
- Security scanning with Docker Scout

### [Browser Tools](tools_and_features/browser_tools.md)
- Playwright browser automation
- Selenium WebDriver integration
- Screenshot capture and analysis
- Web page interaction and testing

### [Documentation Tools](tools_and_features/documentation_tools.md)
- Access to 700+ documentation sources
- Multi-language documentation support
- Search and retrieval capabilities
- DevDocs integration

### [Development Tools](tools_and_features/development_tools.md)
- Code analysis and linting
- Test execution and reporting
- Build process automation
- Development environment setup

### [Monitoring Tools](tools_and_features/monitoring_tools.md)
- Container resource monitoring
- System health checks
- Performance metrics
- Log analysis

### [Workflow Tools](tools_and_features/workflow_tools.md)
- Automated workflows
- Task orchestration
- Pipeline management
- CI/CD integration

## Usage Examples

### Basic Container Operations
```python
# Create a new container
container = await create_container(
    image="python:3.11-slim",
    name="my-dev-container"
)

# Execute commands
result = await execute_command(
    container_id=container.id,
    command="python --version"
)
```

### Documentation Search
```python
# Search Python documentation
docs = await search_language_docs(
    language="python",
    query="async await",
    max_results=5
)
```

### Browser Automation
```python
# Launch browser and navigate
browser = await playwright_launch_browser(browser_type="chromium")
page = await playwright_create_page(browser_id=browser.id)
await playwright_navigate(page_id=page.id, url="https://example.com")
```

For more detailed examples, see [Usage Examples](examples/usage_examples.md).

## Security

The MCP Docker Developer Server includes several security features:
- Container isolation and sandboxing
- Configurable security levels (LOW, MEDIUM, HIGH, STRICT)
- Resource limits and quotas
- Docker Scout security scanning
- Access control and authentication

## Troubleshooting

Common issues and solutions can be found in our [Troubleshooting Guide](troubleshooting/troubleshooting.md).

## API Reference

For complete API documentation, see [API Reference](api/api_reference.md).

## Contributing

This project is designed to be a comprehensive development tool. For contributions and feature requests, please refer to the main repository.
