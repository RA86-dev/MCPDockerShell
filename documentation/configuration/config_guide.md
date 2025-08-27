# The Complete Configuration Guide to MCP Developer Server (MCPDS)
This contains the complete guide to configure the MCPDS server. 
## Configuration with GPUs
To configure MCP Developer Server, please visit the compose file. It contains the entirety of all the features that can be added.
### Configuration with NVIDIA:
To configure MCP Developer Server, please follow the guide:
#### Prequisites:
- MCP Server downloaded using git (complete via `git clone https://github.com/RA86-dev/MCPDockerShell`)
- NVIDIA GPU and NVIDIA drivers
- NVIDIA Container Toolkit (learn more at [Nvidia's Installation Guide for Datacenter](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html))
#### Installation
First, configure the compose.yml file that is in the home folder. Uncomment the section that contains the NVIDIA GPU features.

Afterwards, run `docker compose up -d --build` to compile and build the new docker compose.
### Configuration with AMD
AMD Configuration settings requires the following specifications.
#### Prequisites
- ROCm Drivers installed
- ROCm