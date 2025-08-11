# Transport Methods (HTTP/SSE)

This guide explains how to run MCPDocker using HTTP or Server-Sent Events (SSE) transport methods, which are ideal for web applications, remote access, and custom integrations.

## Overview

MCPDocker supports three transport methods:
- **stdio**: Default mode for Claude Desktop integration
- **sse**: Server-Sent Events for real-time web applications
- **http**: HTTP transport for web APIs and remote access

## Prerequisites

1. **MCPDocker installed**: Follow the [Getting Started guide](start.md)
2. **Docker running**: Ensure Docker is installed and running
3. **Network access**: Ensure the port you choose is available

## HTTP Transport

### Basic Usage

#### Using uv (Recommended):
```bash
# Clone and setup
git clone https://github.com/RA86-dev/MCPDockerShell.git
cd MCPDocker

# Install dependencies
uv sync

# Run with HTTP transport
uv run main.py --transport http
```

#### Using pip:
```bash
# Clone and setup
git clone https://github.com/RA86-dev/MCPDockerShell.git
cd MCPDocker

# Install dependencies
pip install -r requirements.txt

# Run with HTTP transport
python main.py --transport http
```

### Accessing the HTTP Interface

Once started, MCPDocker will be available at:
- **Local access**: `http://localhost:8080`
- **Network access**: `http://YOUR_IP:8080`

### HTTP API Examples

#### Create a Container
```bash
curl -X POST http://localhost:8080/tools/create_container \
  -H "Content-Type: application/json" \
  -d '{
    "image": "ubuntu:latest",
    "name": "my-container",
    "use_gpu": false
  }'
```

#### Execute Command
```bash
curl -X POST http://localhost:8080/tools/execute_command \
  -H "Content-Type: application/json" \
  -d '{
    "container_id": "container_id_here",
    "command": "ls -la"
  }'
```

#### List Containers
```bash
curl http://localhost:8080/tools/list_containers
```

## Server-Sent Events (SSE)

### Basic Usage

#### Using uv:
```bash
uv run main.py --transport sse
```

#### Using pip:
```bash
python main.py --transport sse
```

### SSE Client Example

```javascript
// Connect to SSE endpoint
const eventSource = new EventSource('http://localhost:8080/sse');

// Listen for messages
eventSource.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};

// Send commands
async function sendCommand(tool, params) {
    const response = await fetch('http://localhost:8080/tools/' + tool, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(params)
    });
    return response.json();
}

// Example: Create container
sendCommand('create_container', {
    image: 'python:latest',
    name: 'python-env'
});
```

## Configuration Options

### Custom Port
By default, MCPDocker runs on port 8080. To use a different port:

```bash
# Set environment variable
export MCPDOCKER_PORT=3000

# Then run normally
uv run main.py --transport http
```

### Binding to All Interfaces
To allow external connections (be careful with security):

```bash
# Set bind address
export MCPDOCKER_HOST=0.0.0.0

# Run the server
uv run main.py --transport http
```

## Integration Examples

### Python Client
```python
import requests
import json

class MCPDockerClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
    
    def create_container(self, image, name=None, use_gpu=False):
        response = requests.post(
            f"{self.base_url}/tools/create_container",
            json={
                "image": image,
                "name": name,
                "use_gpu": use_gpu
            }
        )
        return response.json()
    
    def execute_command(self, container_id, command):
        response = requests.post(
            f"{self.base_url}/tools/execute_command",
            json={
                "container_id": container_id,
                "command": command
            }
        )
        return response.json()
    
    def list_containers(self):
        response = requests.get(f"{self.base_url}/tools/list_containers")
        return response.json()

# Usage example
client = MCPDockerClient()
result = client.create_container("ubuntu:latest", "test-container")
print(result)
```

### Node.js Client
```javascript
const axios = require('axios');

class MCPDockerClient {
    constructor(baseUrl = 'http://localhost:8080') {
        this.baseUrl = baseUrl;
    }
    
    async createContainer(image, name = null, useGpu = false) {
        const response = await axios.post(`${this.baseUrl}/tools/create_container`, {
            image,
            name,
            use_gpu: useGpu
        });
        return response.data;
    }
    
    async executeCommand(containerId, command) {
        const response = await axios.post(`${this.baseUrl}/tools/execute_command`, {
            container_id: containerId,
            command
        });
        return response.data;
    }
    
    async listContainers() {
        const response = await axios.get(`${this.baseUrl}/tools/list_containers`);
        return response.data;
    }
}

// Usage example
(async () => {
    const client = new MCPDockerClient();
    const result = await client.createContainer('node:latest', 'node-env');
    console.log(result);
})();
```

## Security Considerations

### Important Security Notes
- **Local development only**: By default, MCPDocker only binds to localhost
- **No authentication**: HTTP/SSE modes don't include authentication
- **Firewall protection**: Ensure your firewall blocks external access if not needed
- **Container isolation**: Containers still run in isolated environments

### Production Deployment
For production use, consider:
- Setting up a reverse proxy with authentication
- Using HTTPS/TLS encryption
- Implementing proper access controls
- Monitoring and logging

## Troubleshooting

### Port Already in Use
```bash
# Check what's using port 8080
lsof -i :8080

# Use a different port
export MCPDOCKER_PORT=8081
uv run main.py --transport http
```

### Connection Refused
- Ensure Docker is running
- Check if the port is accessible
- Verify firewall settings

### Service Not Responding
- Check server logs for errors
- Verify Python dependencies are installed
- Ensure sufficient system resources

## Advanced Usage

### Custom FastAPI Configuration
You can customize the FastAPI server by modifying the main.py file or using environment variables:

```bash
# Enable debug mode
export MCPDOCKER_DEBUG=true

# Set custom host and port
export MCPDOCKER_HOST=0.0.0.0
export MCPDOCKER_PORT=8000

# Run with custom settings
uv run main.py --transport http
```

### Load Balancing
For high availability, you can run multiple instances behind a load balancer:

```bash
# Instance 1
MCPDOCKER_PORT=8080 uv run main.py --transport http

# Instance 2  
MCPDOCKER_PORT=8081 uv run main.py --transport http

# Instance 3
MCPDOCKER_PORT=8082 uv run main.py --transport http
```

## Getting Help

If you encounter issues:
1. Check the [Getting Started guide](start.md) for basic setup
2. Verify Docker is running and accessible
3. Check network connectivity and firewall settings
4. Review server logs for specific error messages