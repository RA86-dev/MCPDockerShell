# Installation Guide

This guide provides comprehensive installation instructions for the MCP Docker Developer Server, including system requirements, installation steps, and post-installation configuration.

## System Requirements

### Minimum Requirements

- **RAM**: 6 GB
- **CPU**: 2 cores minimum
- **Storage**: 15 GB free space
- **Architecture**: AMD64  only.
- **Operating System**: Linux, macOS, or Windows with WSL2

### Recommended Specifications

- **RAM**: 8 GB or more
- **CPU**: 4+ cores
- **Storage**: 30 GB free space
- **Architecture**: x86_64 Architecture
- **Network**: Stable internet connection for documentation downloads

### Prerequisites

Before installation, ensure you have:

- **Docker Engine**: Version 20.10 or later
- **Docker Compose**: Version 2.0 or later  
- **Git**: Version 2.0 or later
- **Node.js and npm**: For Claude Desktop integration (optional)

## Installation Methods

### Method 1: Docker Compose (Recommended)

This method installs the complete MCP Docker Developer Server stack including documentation services.

#### Step 1: Clone the Repository

```bash
git clone https://github.com/RA86-dev/MCPDockerShell.git
cd MCPDockerShell
```

#### Step 2: Configure the Environment

Edit the `compose.yml` file to customize your installation:

```yaml
# Key configuration options in compose.yml
services:
  mcpdocker:
    environment:
      - SECURITY_LEVEL=MEDIUM    # LOW, MEDIUM, HIGH, STRICT
      - MCP_LOG_LEVEL=INFO       # DEBUG, INFO, WARNING, ERROR
      - MAX_CONTAINERS=10        # Maximum containers to allow
```

#### Step 3: Launch the Services

```bash
# Start all services in detached mode
docker compose up -d --build
```

#### Step 4: Verify Installation

```bash
# Check that all services are running
docker ps

# You should see containers for:
# - mcpdocker-server
# - mcpdocker-devdocs  
# - mcpdocker-devdocs-sync
```

### Method 2: Standalone Docker Container

For a minimal installation with just the core MCP server:

```bash
# Pull and run the MCP Docker server
docker run -d \
  --name mcp-docker-server \
  -p 3000:3000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v mcp-workspace:/workspace \
  mcpdocker:latest
```

### Method 3: Development Installation

For development and customization:

```bash
# Clone the repository
git clone https://github.com/RA86-dev/MCPDockerShell.git
cd MCPDockerShell

# Build the development image
docker build -t mcpdocker:dev .

# Run with development settings
docker run -d \
  --name mcp-docker-dev \
  -p 3000:3000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/app \
  -e DEVELOPMENT_MODE=true \
  -e DEBUG_ENABLED=true \
  mcpdocker:dev
```

## GPU Support Installation (Optional)

### NVIDIA GPU Support

For AI/ML workloads requiring GPU acceleration:

#### Step 1: Install NVIDIA Container Toolkit

**Ubuntu/Debian:**
```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-container-toolkit
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker
```

**CentOS/RHEL:**
```bash
# Add NVIDIA package repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/centos7/nvidia-docker.repo | \
  sudo tee /etc/yum.repos.d/nvidia-docker.repo

# Install nvidia-container-toolkit
sudo yum install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker
```

#### Step 2: Enable GPU in Docker Compose

```yaml
# Add to compose.yml
services:
  mcpdocker:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

### AMD GPU Support (ROCm)

For AMD GPU support with ROCm:

```bash
# Install ROCm Docker support
# Ubuntu/Debian
wget -qO - https://repo.radeon.com/rocm/rocm.gpg.key | sudo apt-key add -
echo 'deb [arch=amd64] https://repo.radeon.com/rocm/apt/debian/ xenial main' | \
  sudo tee /etc/apt/sources.list.d/rocm.list
sudo apt update && sudo apt install rocm-dkms
```

## Network Configuration


### Firewall Configuration

Ensure these ports are accessible:

- **8000**: MCP Server API
- **9292**: DevDocs documentation server
- **8888**: SearXNG search engine 

**Ubuntu/Debian (ufw):**
```bash
sudo ufw allow 3000/tcp
sudo ufw allow 9292/tcp
```

**CentOS/RHEL (firewalld):**
```bash
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --permanent --add-port=9292/tcp
sudo firewall-cmd --reload
```

### Remote Access Configuration

For remote access or server deployments:

1. **Update IP Configuration**: Edit `configuration.json` to reflect your server's IP address
2. **Configure Reverse Proxy**: Set up nginx or Apache for HTTPS termination
3. **Security**: Implement authentication and access controls

## Claude Desktop Integration

### Step 1: Install Claude Desktop

Download and install Claude Desktop from the official website.

### Step 2: Configure MCP Integration

1. Open Claude Desktop
2. Click your profile icon → Settings → Developer
3. Select "Edit Configuration"
4. Add the MCP server configuration:

```json
{
  "mcpServers": {
    "mcp-docker-developer": {
      "command": "docker",
      "args": [
        "run", "--rm", "-i",
        "--name", "mcp-docker-server",
        "-p", "3000:3000", 
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-v", "mcp-workspace:/workspace",
        "mcpdocker:latest"
      ]
    }
  }
}
```

### Step 3: Verify Integration

1. Completely close and reopen Claude Desktop
2. Start a new conversation
3. Look for MCP tools in the available tools list
4. Test with a simple command like listing containers

## Post-Installation Configuration

### Initial Setup

1. **Verify Services**:
   ```bash
   # Check all services are running
   docker compose ps
   
   # Check logs for any errors
   docker compose logs
   ```

2. **Test Basic Functionality**:
   ```bash
   # Test the MCP server endpoint
   curl http://localhost:3000/health
   
   # Test DevDocs integration
   curl http://localhost:9292
   ```

3. **Download Documentation** (Optional):
   ```bash
   # Access the DevDocs sync container to download docs
   docker exec mcpdocker-devdocs-sync python sync_docs.py
   ```

### Security Configuration

1. **Generate Secure Keys**:
   ```bash
   # Generate a secure secret key
   openssl rand -hex 32
   ```

2. **Set Environment Variables**:
   ```bash
   # Add to your environment or .env file
   export MCP_SECRET_KEY="your-generated-key-here"
   export SECURITY_LEVEL="MEDIUM"
   ```

3. **Configure Access Controls**: Review and adjust security settings in `compose.yml`

### Performance Optimization

1. **Resource Limits**: Adjust container resource limits based on your system
2. **Docker Configuration**: Optimize Docker daemon settings
3. **Storage**: Configure appropriate storage drivers and volumes

## Troubleshooting Installation

### Common Issues

#### Docker Socket Permission Issues
```bash
# Fix Docker socket permissions
sudo chmod 666 /var/run/docker.sock
# Or add user to docker group
sudo usermod -aG docker $USER
# Then logout and login again
```

#### Port Conflicts
```bash
# Check if ports are in use
sudo lsof -i :3000
sudo lsof -i :9292

# Change ports in compose.yml if needed
```

#### Memory Issues
```bash
# Check available memory
free -h

# Increase swap if needed (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### Network Connectivity
```bash
# Test Docker network connectivity
docker network ls
docker network inspect mcp-network

# Test external connectivity from containers
docker run --rm alpine ping -c 3 google.com
```

### Log Analysis

Check logs for troubleshooting:

```bash
# View all service logs
docker compose logs

# View specific service logs
docker compose logs mcpdocker
docker compose logs devdocs

# Follow logs in real-time
docker compose logs -f
```

## Advanced Installation Options

### Custom Docker Images

Build custom images with additional tools:

```dockerfile
# Custom Dockerfile
FROM mcpdocker:latest

# Add custom tools
RUN apt-get update && apt-get install -y \
    custom-tool-1 \
    custom-tool-2

# Add custom configuration
COPY custom-config.json /app/config/
```

### Multi-Node Setup

For distributed installations:

```yaml
# Multi-node compose configuration
version: '3.8'
services:
  mcpdocker-node1:
    image: mcpdocker:latest
    environment:
      - NODE_ID=node1
      - CLUSTER_MODE=true
    
  mcpdocker-node2:
    image: mcpdocker:latest
    environment:
      - NODE_ID=node2
      - CLUSTER_MODE=true
```

### Kubernetes Deployment

For Kubernetes environments:

```yaml
# kubernetes-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcpdocker
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mcpdocker
  template:
    metadata:
      labels:
        app: mcpdocker
    spec:
      containers:
      - name: mcpdocker
        image: mcpdocker:latest
        ports:
        - containerPort: 3000
        volumeMounts:
        - name: docker-sock
          mountPath: /var/run/docker.sock
      volumes:
      - name: docker-sock
        hostPath:
          path: /var/run/docker.sock
```

## Maintenance and Updates

### Regular Updates

```bash
# Update to latest version
docker compose pull
docker compose up -d --build

# Clean up old images
docker image prune
```

### Backup and Restore

```bash
# Backup data volumes
docker run --rm -v mcp-workspace:/source -v $(pwd):/backup alpine \
  tar -czf /backup/mcp-backup.tar.gz -C /source .

# Restore from backup
docker run --rm -v mcp-workspace:/target -v $(pwd):/backup alpine \
  tar -xzf /backup/mcp-backup.tar.gz -C /target
```

This installation guide provides comprehensive instructions for setting up the MCP Docker Developer Server in various environments and configurations.
