# Getting Started with MCPDocker

This guide will help you install and set up MCPDocker for use with AI assistants.

## Prerequisites

Before installing MCPDocker, ensure you have the following installed:

### Required
- **Docker Engine or Docker Desktop**: [Download here](https://docs.docker.com/get-docker/)
- **Python 3.11 or higher**: [Download here](https://www.python.org/downloads/)

### Optional (Recommended)
- **uv**: Fast Python package manager - [Installation guide](https://docs.astral.sh/uv/getting-started/installation/)
- **NVIDIA Drivers**: For GPU support (if you have an NVIDIA GPU)

## Installation Methods

### Method 1: Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/RA86-dev/MCPDockerShell.git
cd MCPDocker

# Install dependencies with uv
uv sync

# Run MCPDocker
uv run main.py
```

### Method 2: Using pip

```bash
# Clone the repository  
git clone https://github.com/RA86-dev/MCPDockerShell.git
cd MCPDocker

# Create a virtual environment (recommended)
python -m venv mcpdocker-env
source mcpdocker-env/bin/activate  # On Windows: mcpdocker-env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run MCPDocker
python main.py
```

## Setup Methods

MCPDocker can be configured in two ways:

### 🖥️ Claude Desktop Integration
Best for personal use with Claude Desktop application.
- **[Setup Guide](Claude.md)** - Configure MCPDocker with Claude Desktop

### 🌐 Transport Methods (HTTP/SSE)
Best for web applications and remote access.
- **[Setup Guide](transport.md)** - Configure HTTP or SSE transport

## Verification

To verify your installation is working:

1. **Check Docker is running:**
   ```bash
   docker version
   ```

2. **Test MCPDocker:**
   ```bash
   # Using uv
   uv run main.py --help
   
   # Or using pip
   python main.py --help
   ```

3. **Check GPU support (if available):**
   ```bash
   nvidia-smi  # Should show your GPU information
   ```

## Troubleshooting

### Common Issues

**Docker not found:**
- Ensure Docker is installed and running
- Check that your user has permission to run Docker commands

**Python version error:**
- MCPDocker requires Python 3.11+
- Check your version with `python --version`

**Permission errors:**
- On Linux/macOS, you may need to add your user to the docker group:
  ```bash
  sudo usermod -aG docker $USER
  ```
- Log out and back in for changes to take effect

**GPU support not detected:**
- Ensure NVIDIA drivers are installed
- Install nvidia-docker: `sudo apt-get install nvidia-docker2` (Ubuntu)
- Ensure that you have the NVIDIA Container Toolkit ([Visit here](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html))

- Restart Docker daemon after installation
## 
## Next Steps

Once installed, proceed with your preferred setup method:
- **For Claude Desktop users**: Follow the [Claude Desktop Setup Guide](Claude.md)
- **For web/remote usage**: Follow the [Transport Methods Guide](transport.md)