# MCP Developer Server (MCPDS)
MCP Developer Server (MCPDS) is a MCP Server made in python designed for Developers. It can acess over 700+ different documentations (using devdocs.io's self-hosted docker container), and can also create docker containers to run modularized testing inside those containers. It can also use an **NVIDIA GPU** if NVIDIA's toolkit is installed, and setup for Docker.
## Examples

Reading Documentation and Summarizing it:


<video width="640" height="480" controls>
    <source type="video/mp4" src="README_assets/ReadingDocu.mp4"></source>
</video>

Creating a React Project:

<video width="640" height="480" controls>
    <source type="video/mp4" src="README_assets/creatingcode.mp4">
</video>

## Requirements
This section covers the minimum requirements for the MCP Developer Server.
### Base Specifications
(This server does not use a lot of CPU, so the minimum is very low.)
- 6 GB of RAM
- 15 GB of extra space
- 2 core CPU.
- ARM64 or AMD64. ARM64 is less supported, as `devdocs` does not have a ARM64 container, but still works.
### Recommended Specifications:
- 10 GB of RAM
- 30 GB of extra space
- 4+ core CPU running x86.
## Installation
To install MCP Developer Server, you can use Docker or just straight up run it.
### Docker Installation (**Recommended**)
To install Docker, please ensure that you have Docker compose and Docker. (depending on if you are running `docker compose` or `docker-compose`, please change the command to your docker compose element).

To install, copy the following commands:
```
git clone https://github.com/RA86-dev/MCPDocker
cd MCPDocker
docker compose up -d
```
This will automatically set up the instances `devdocs`, `devdocs-sync` (devdocs does not sync), and `mcpdocker`. **MCP Docker will connect to the Socket instance, so it can see running containers and run containers.**
### Base installation
To install it locally, please run the following commands:
```
git clone https://github.com/RA86-dev/MCPDocker
cd MCPDocker
python3 -m venv .venv
```
Enter the virtualized environment based on your platform. Then run the next commands:
```
pip install -r requirements.txt
python3 main.py --transport sse
```
## The Setup for Configuration
If you are running this on a server, or using a Cloudflare Tunnel, you will need to change the IP Address to the active location where it is running, or just click on Custom Connectors and use like that. To set it up, please use `configuration.json`'s configuration to setup.
### Claude Desktop
To set up MCP Docker Server for Claude Desktop, open up the application. Click on your icon and select Developer in the settings. Click Edit Configuration and add the configuratory details from the configuration.json file. Then, Close and reopen Claude (completely) to let Claude refresh the new MCP server. You should see the MCP Server now setup!

For more information, visit [Model Context Protocol's Connect to Local MCP Server Guide.](http://modelcontextprotocol.io/quickstart/user)
## Recommendations and Prompts
The best prompts to use with this MCP Server is in `prompt.xml`. It is regularly updated for AI's to use. It uses XML format so that the AI can differentiate different portions of the prompt from one another.
