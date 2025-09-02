# MCP Docker Developer Server Documentation

MCP Developer Server is a Python-based MCP (Model Context Protocol) server designed to supercharge your development workflow. It provides instant access to 700+ documentation sources and creates isolated Docker containers for safe code testing and experimentation.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Tools and Features](#tools-and-features)
5. [Usage Examples](#usage-examples)
6. [Troubleshooting](#troubleshooting)

## Getting Started

The MCP Docker Developer Server combines two powerful capabilities:

### Documentation Access
- Access over 700 programming language and framework documentation sources via a local DevDocs instance.
- Search across multiple documentation sources simultaneously.
- Get summaries, examples, and detailed explanations.

### Containerized Development
- Create isolated Docker containers for safe code testing.
- Support for a wide range of popular programming languages and frameworks.
- Optional NVIDIA GPU acceleration for AI/ML workloads.

## Installation

See [Installation Guide](installation/install_docker.md) for detailed setup instructions.

## Configuration

For detailed configuration options, see [Configuration Guide](configuration/config_guide.md).

## Tools and Features

The MCP Docker Developer Server provides several categories of tools:

### [Docker Tools](tools_and_features/docker_tools.md)
- Container management (create, start, stop, delete, inspect).
- Command execution inside containers.
- A shared workspace for file management.
- GPU status monitoring.

### [Documentation Tools](tools_and_features/documentation_tools.md)
- Search and retrieve content from the DevDocs instance.
- List available documentation sets.
- Get quick-reference guides for popular languages.

*Note: The other tool categories (Browser, Development, Monitoring, Workflow) are not fully implemented yet.*

## Usage Examples

Here are a few simple examples of what you can do with the server. For more detailed examples, see the [Usage Examples](examples/usage_examples.md) guide.

### Basic Container Operations
```python
# Create a new container
await create_container(
    image="python:3.11",
    name="my-dev-container"
)

# Execute a command in the container
result = await execute_command(
    container_id="my-dev-container",
    command="python --version"
)
```

### Documentation Search
```python
# Search Python documentation
docs = await search_devdocs(
    language="python",
    query="async await",
    max_results=5
)
```

## Troubleshooting

Common issues and solutions can be found in our [Troubleshooting Guide](troubleshooting/troubleshooting.md).
