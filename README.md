# MCPDocker

MCPDocker is a Model Context Protocol (MCP) server that provides Docker container management capabilities for AI assistants. It creates a secure, virtualized environment where AI can safely execute code, manage files, and test applications within isolated Docker containers.

## ✨ Key Features

### 🚀 Container Management
- Create, start, stop, and delete Docker containers
- Execute commands within running containers
- Monitor container status and logs
- Support for popular Docker images (Ubuntu, Python, Node.js, etc.)

### 🔧 File Operations
- Upload/download files to shared workspace
- Copy files between host and containers
- Create, read, write, and manage files within containers
- Directory management and file system operations

### 🔒 Security Features
- Docker Scout integration for vulnerability scanning
- Security policy evaluation
- Image comparison and recommendations
- Restricted to pre-approved Docker images

### 🌐 Browser Automation
- **Playwright Support**: Cross-browser automation with Chromium, Firefox, and WebKit
- **Selenium Support**: Traditional WebDriver automation with Chrome and Firefox
- Page navigation, element interaction, and screenshot capabilities
- JavaScript execution and element waiting functionality
- Concurrent browser instance management

### ⚡ Hardware Support
- NVIDIA GPU acceleration support
- Automatic GPU detection and configuration
- GPU-enabled container images when available

### 🌐 Transport Methods
- Standard I/O (stdio) for Claude Desktop integration
- HTTP transport for web applications
- Server-Sent Events (SSE) support

## 📋 Prerequisites

- **Docker**: Docker Engine or Docker Desktop installed and running
- **Python**: Python 3.11 or higher
- **GPU Support (Optional)**: NVIDIA drivers and nvidia-docker for GPU acceleration

## 📖 Documentation

- **[Getting Started](docs/start.md)** - Installation and setup instructions
- **[Claude Desktop Setup](docs/Claude.md)** - Configure MCPDocker with Claude Desktop
- **[Browser Automation](docs/browser-automation.md)** - Playwright and Selenium integration guide
- **[Transport Methods](docs/transport.md)** - Alternative connection methods

## 🚧 Work in Progress

- External port mapping support
- Additional container networking features
- Enhanced monitoring and logging capabilities