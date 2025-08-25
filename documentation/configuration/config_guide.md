# Configuration Guide

This guide covers the comprehensive configuration options available for the MCP Docker Developer Server, including service configuration, security settings, resource limits, and integration options.

## Overview

The MCP Docker Developer Server uses a flexible configuration system that allows you to:

- Enable/disable specific tool categories
- Configure security levels and access controls
- Set resource limits and quotas
- Customize Docker container settings
- Configure external service integrations
- Set up monitoring and logging options

## Configuration Files

### Main Configuration File (configuration.json)

The primary configuration file contains Claude Desktop integration settings and server connection details:

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
        "mcp-docker:latest"
      ]
    }
  }
}
```

### Docker Compose Configuration (compose.yml)

The Docker Compose file defines the complete service stack:

```yaml
version: '3.8'

services:
  # Main MCP Docker Server
  mcpdocker:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: mcpdocker-server
    ports:
      - "3000:3000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - mcp-workspace:/workspace
      - ./data:/app/data
    environment:
      - DEVDOCS_URL=http://devdocs:9292
      - SEARXNG_URL=http://searxng:8888
      - MCP_LOG_LEVEL=INFO
      - SECURITY_LEVEL=MEDIUM
    depends_on:
      - devdocs
    networks:
      - mcp-network

  # Documentation Server (DevDocs)
  devdocs:
    image: thibautcornolti/devdocs:latest
    container_name: mcpdocker-devdocs
    ports:
      - "9292:9292"
    volumes:
      - devdocs-data:/devdocs/public/docs
    networks:
      - mcp-network

  # Documentation Synchronization
  devdocs-sync:
    build:
      context: .
      dockerfile: Dockerfile.sync
    container_name: mcpdocker-devdocs-sync
    volumes:
      - devdocs-data:/devdocs/public/docs
    depends_on:
      - devdocs
    networks:
      - mcp-network

volumes:
  mcp-workspace:
  devdocs-data:

networks:
  mcp-network:
    driver: bridge
```

## Service Configuration

### Tool Categories Configuration

Control which tool categories are enabled:

```python
# Service configuration in main.py
service_config = ServiceConfig(
    docker_management=True,      # Enable Docker tools
    browser_automation=True,     # Enable browser tools
    monitoring_tools=True,       # Enable monitoring tools
    development_tools=True,      # Enable development tools
    workflow_tools=True,         # Enable workflow tools
    documentation_tools=True,    # Enable documentation tools
    firecrawl_tools=False,      # Disable Firecrawl tools
    searxng_tools=False         # Disable SearXNG tools
)
```

### Security Configuration

Configure security levels and access controls:

```python
# Security levels
class SecurityLevel(str, Enum):
    LOW = "low"          # Minimal restrictions
    MEDIUM = "medium"    # Balanced security
    HIGH = "high"        # Strict security
    STRICT = "strict"    # Maximum security

# Security configuration
SECURITY_LEVEL = SecurityLevel.MEDIUM
```

#### Security Level Details

**LOW Security:**
- Minimal container restrictions
- Broad network access
- Basic authentication
- Extended timeouts

**MEDIUM Security:**
- Standard container isolation
- Controlled network access
- Token-based authentication
- Standard timeouts

**HIGH Security:**
- Enhanced container isolation
- Restricted network access
- Multi-factor authentication
- Shorter timeouts

**STRICT Security:**
- Maximum container isolation
- No external network access
- Advanced authentication
- Minimal timeouts

## Environment Variables

### Core Environment Variables

```bash
# Server Configuration
MCP_HOST=localhost
MCP_PORT=3000
MCP_LOG_LEVEL=INFO
MCP_SECRET_KEY=your-secret-key-here

# Security Configuration
SECURITY_LEVEL=MEDIUM
ENABLE_AUTHENTICATION=true
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Resource Limits
MAX_CONTAINERS=10
MAX_WORKERS=10
REQUEST_TIMEOUT=30
CONTAINER_TIMEOUT=300

# External Services
DEVDOCS_URL=http://devdocs:9292
SEARXNG_URL=http://searxng:8888

# Docker Configuration
DOCKER_API_VERSION=auto
DOCKER_HOST=unix:///var/run/docker.sock

# Cache Configuration
CACHE_TTL=300
MAX_CACHE_SIZE=1000

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

### Development Environment Variables

```bash
# Development Settings
DEVELOPMENT_MODE=true
DEBUG_ENABLED=true
HOT_RELOAD=true
VERBOSE_LOGGING=true

# Testing Configuration
TEST_MODE=false
MOCK_EXTERNAL_SERVICES=false
TEST_DATA_PATH=/app/test-data
```

### Production Environment Variables

```bash
# Production Settings
DEVELOPMENT_MODE=false
DEBUG_ENABLED=false
ENABLE_METRICS=true
ENABLE_HEALTH_CHECKS=true

# Performance Optimization
WORKER_PROCESSES=4
CONNECTION_POOL_SIZE=20
ASYNC_TASK_WORKERS=8

# Monitoring
METRICS_ENDPOINT=/metrics
HEALTH_CHECK_ENDPOINT=/health
MONITORING_INTERVAL=30
```

## Resource Configuration

### Container Resource Limits

Configure default resource limits for created containers:

```yaml
# Resource limits configuration
container_defaults:
  memory_limit: "1GB"
  cpu_limit: "1.0"
  swap_limit: "512MB"
  disk_limit: "10GB"
  
  # Network settings
  network_mode: "bridge"
  port_range: "8000-8999"
  
  # Security settings
  read_only_root_fs: false
  no_new_privileges: true
  user: "1000:1000"
```

### System Resource Configuration

```yaml
# System resource configuration
system_limits:
  max_concurrent_containers: 10
  max_container_memory: "8GB"
  max_total_cpu: "4.0"
  max_disk_usage: "50GB"
  
  # Cleanup settings
  container_ttl: "24h"
  cleanup_interval: "1h"
  orphaned_container_cleanup: true
```

## Docker Configuration

### Allowed Images Configuration

Configure which Docker images can be used:

```python
# Allowed Docker images
ALLOWED_IMAGES = [
    # Programming Languages
    "python:3.11-slim",
    "python:3.10-slim", 
    "python:3.9-slim",
    "node:18-alpine",
    "node:16-alpine",
    "openjdk:17-alpine",
    "golang:1.21-alpine",
    "rust:1.70-slim",
    
    # Databases
    "postgres:15-alpine",
    "mysql:8.0",
    "redis:7-alpine",
    "mongodb:6.0",
    
    # Web Servers
    "nginx:alpine",
    "httpd:alpine",
    
    # Development Tools
    "ubuntu:22.04",
    "alpine:latest"
]
```

### GPU Configuration

Enable GPU support for containers:

```yaml
# GPU configuration
gpu_support:
  enabled: true
  runtime: "nvidia"
  capabilities: ["gpu"]
  
  # GPU resource limits
  device_requests:
    - driver: "nvidia"
      count: 1
      capabilities: [["gpu"]]
```

## Monitoring and Logging Configuration

### Logging Configuration

```yaml
# Logging configuration
logging:
  level: INFO
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  
  # Log rotation
  max_size: "100MB"
  backup_count: 5
  
  # Log destinations
  console: true
  file: "/app/logs/mcpdocker.log"
  
  # Structured logging
  structured: true
  include_request_id: true
```

### Monitoring Configuration

```yaml
# Monitoring configuration
monitoring:
  enabled: true
  metrics_port: 9090
  health_check_interval: 30
  
  # Metrics collection
  collect_system_metrics: true
  collect_container_metrics: true
  collect_application_metrics: true
  
  # External monitoring
  prometheus:
    enabled: true
    endpoint: "/metrics"
  
  grafana:
    enabled: false
    dashboard_url: "http://grafana:3000"
```

## Network Configuration

### Port Configuration

```yaml
# Network configuration
networking:
  # Server ports
  server_port: 3000
  metrics_port: 9090
  health_port: 8080
  
  # Container networking
  default_network: "mcp-network"
  create_networks: true
  
  # Port ranges for containers
  container_port_range:
    start: 8000
    end: 8999
  
  # External access
  allow_external_access: false
  whitelist_ips: []
```

### Proxy Configuration

```yaml
# Proxy configuration (if behind a proxy)
proxy:
  enabled: false
  http_proxy: "http://proxy.company.com:8080"
  https_proxy: "https://proxy.company.com:8080"
  no_proxy: "localhost,127.0.0.1,devdocs,searxng"
```

## Database Configuration

### SQLite Configuration (Default)

```yaml
# SQLite configuration
database:
  type: "sqlite"
  path: "/app/data/mcpdocker.db"
  
  # Connection settings
  timeout: 30
  check_same_thread: false
  
  # Performance settings
  journal_mode: "WAL"
  synchronous: "NORMAL"
  cache_size: 10000
```

### PostgreSQL Configuration (Optional)

```yaml
# PostgreSQL configuration
database:
  type: "postgresql"
  host: "postgres"
  port: 5432
  database: "mcpdocker"
  username: "mcpuser"
  password: "secure-password"
  
  # Connection pool
  pool_size: 10
  max_overflow: 20
  pool_timeout: 30
```

## External Service Integration

### DevDocs Configuration

```yaml
# DevDocs integration
devdocs:
  url: "http://devdocs:9292"
  timeout: 30
  
  # Synchronization settings
  sync_enabled: true
  sync_interval: "24h"
  auto_download: true
  
  # Language priorities
  priority_languages:
    - python
    - javascript
    - java
    - go
    - rust
```

### Browser Automation Configuration

```yaml
# Browser automation settings
browser_automation:
  # Default browser settings
  default_browser: "chromium"
  headless: true
  
  # Resource limits
  max_browsers: 5
  browser_timeout: 300
  
  # Screenshot settings
  screenshot_format: "png"
  screenshot_quality: 80
  max_screenshot_size: "5MB"
```

## Configuration Validation

### Environment Validation

The server validates configuration on startup:

```python
# Configuration validation
def validate_configuration():
    # Check required environment variables
    required_vars = [
        "MCP_SECRET_KEY",
        "DEVDOCS_URL",
        "SECURITY_LEVEL"
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Required environment variable {var} not set")
    
    # Validate security level
    security_level = os.getenv("SECURITY_LEVEL")
    if security_level not in ["LOW", "MEDIUM", "HIGH", "STRICT"]:
        raise ValueError(f"Invalid security level: {security_level}")
    
    # Validate resource limits
    max_containers = int(os.getenv("MAX_CONTAINERS", "10"))
    if max_containers < 1 or max_containers > 100:
        raise ValueError(f"Invalid max_containers: {max_containers}")
```

## Configuration Templates

### Development Configuration Template

```yaml
# Development environment template
version: '3.8'
services:
  mcpdocker:
    build: .
    environment:
      - DEVELOPMENT_MODE=true
      - DEBUG_ENABLED=true
      - MCP_LOG_LEVEL=DEBUG
      - SECURITY_LEVEL=LOW
    ports:
      - "3000:3000"
      - "9090:9090"  # Metrics port
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./:/app  # Mount source code for hot reload
```

### Production Configuration Template

```yaml
# Production environment template
version: '3.8'
services:
  mcpdocker:
    image: mcpdocker:latest
    environment:
      - DEVELOPMENT_MODE=false
      - DEBUG_ENABLED=false
      - MCP_LOG_LEVEL=INFO
      - SECURITY_LEVEL=HIGH
    ports:
      - "3000:3000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - mcp-data:/app/data
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

## Configuration Best Practices

### Security Best Practices

1. **Use Strong Secrets**: Generate secure random keys for MCP_SECRET_KEY
2. **Appropriate Security Levels**: Use HIGH or STRICT for production
3. **Network Isolation**: Limit network access where possible
4. **Regular Updates**: Keep Docker images and dependencies updated

### Performance Best Practices

1. **Resource Limits**: Set appropriate resource limits based on your system
2. **Monitoring**: Enable monitoring and metrics collection
3. **Caching**: Configure appropriate cache settings
4. **Connection Pooling**: Use connection pooling for databases

### Maintenance Best Practices

1. **Configuration Version Control**: Store configuration in version control
2. **Environment Separation**: Use different configurations for different environments
3. **Regular Backups**: Backup configuration and data regularly
4. **Documentation**: Document custom configuration changes

This configuration guide provides comprehensive coverage of all available configuration options for the MCP Docker Developer Server.