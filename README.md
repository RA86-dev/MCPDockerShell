# MCP Developer Server (MCPDS)

**A powerful development tool that combines comprehensive documentation access with containerized code testing**

MCP Developer Server is a Python-based MCP (Model Context Protocol) server designed to supercharge your development workflow. It provides instant access to 700+ documentation sources and creates isolated Docker containers for safe code testing and experimentation.

## 🚀 What Can It Do?

**Documentation at Your Fingertips**
- Access over 700 programming language and framework docs instantly
- Get summaries, examples, and detailed explanations
- Search across multiple documentation sources simultaneously

**Containerized Development Environment**
- Spin up isolated Docker containers for testing code
- Run experiments without affecting your main system
- Support for multiple programming languages and frameworks
- Optional NVIDIA GPU acceleration for AI/ML workloads

## 📹 See It in Action

**Reading and Summarizing Documentation:**
<video width="640" height="480" controls>
    <source type="video/mp4" src="README_assets/ReadingDocu.mp4">
</video>

If your Editor does not support Videos, visit [README_assets/readingDocu.mp4](README_assets/readingDocu.mp4)


**Creating a React Project:**
<video width="640" height="480" controls>
    <source type="video/mp4" src="README_assets/creatingcode.mp4">
</video>

If your Editor does not support Videos, visit [README_assets/creatingcode.mp4](README_assets/creatingcode.mp4)


## 📋 System Requirements

### Minimum Requirements
- **RAM:** 6 GB
- **Storage:** 15 GB free space
- **CPU:** 2 cores
- **Architecture:** AMD64 

### Recommended Specifications
- **RAM:** 8 GB or more
- **Storage:** 30 GB free space
- **CPU:** 4+ cores
- **Architecture**: x86 Architecture.

### GPU Support (Optional)
- **Supported:** NVIDIA GPUs supported!  (requires NVIDIA Container Toolkit)
- **Supported:** AMD ROCm is supported!

## 🔧 Installation

### ONLY OPTION: Docker Installation (Recommended)

**Prerequisites:**


- Docker and Docker Compose installed on your system
- Node JS and `npx` installed
** Install
This creates three services:
- `devdocs` - Documentation server
- `devdocs-sync` - Documentation synchronization
- `mcpdocker` - Main MCP server with Docker integration


**Installation**


To install this server, please edit the `compose.yml` to your ideal system. It contains a bunch of commented out services or features and more.
Then, install the docker compose server using one command:
```shell
docker compose up -d --build
```

## ⚙️ Configuration

### For Remote/Server Deployments
If running on a server or using Cloudflare Tunnel, update the IP addresses in `configuration.json` to match your setup location.

### Claude Desktop Integration
1. Open Claude Desktop
2. Click your profile icon → Settings → Developer
3. Select "Edit Configuration"
4. Add the configuration details from `configuration.json`
5. Completely close and reopen Claude
6. Verify the MCP Server appears in your tools

For detailed setup instructions, visit the [Model Context Protocol Quick Start Guide](http://modelcontextprotocol.io/quickstart/user).


