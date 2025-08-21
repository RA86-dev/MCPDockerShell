# MCP Developer Docker Server 
MCP Developer Docker Server is a production-level server made for Developers. It contains features such as:
- Selenium
- Playwright
- PyPI, Open Meteo, and Wikipedia
- Python, Go, C#, and more Documentation
## Requirements:
### Minimal
- Docker and Docker Compose Installed.
- 5 GB of Avaliable Memory
- 4 GB of RAM
### Recommended:
- Docker and Docker Compose installed.
- 20 GB of Avaliable Memory
- 8 GB of RAM
## Installation:
To install MCP Developer Docker Server, please run the following commands:
```
git clone https://github.com/RA86-dev/MCPDevServer
cd MCPDevServer
docker compose up -d --build
```
Afterwards, you should run the commands to setup it in Claude Desktop or any other software that needs setup like below:
**claude_desktop_configuration.json**:

```{
  "mcpServers": {
    "docker-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://127.0.0.1:8000/sse",
        "--transport", "sse-only",
        "--allow-http",
        "--debug"
      ]
    }
  }
}
```