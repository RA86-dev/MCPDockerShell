# Troubleshooting Guide

This comprehensive troubleshooting guide helps you diagnose and resolve common issues with the MCP Docker Developer Server.

## Quick Diagnosis

### System Health Check

First, run these commands to check the overall system health:

```bash
# Check if all services are running
docker compose ps

# Check system resources
docker system df
docker system info

# Check logs for errors
docker compose logs --tail=50

# Test MCP server endpoint
curl http://localhost:3000/health

# Test DevDocs service
curl http://localhost:9292
```

### Service Status Indicators

| Service | Port | Health Check | Status |
|---------|------|--------------|--------|
| MCP Server | 3000 | `curl localhost:3000/health` | Should return `{"status": "healthy"}` |
| DevDocs | 9292 | `curl localhost:9292` | Should return HTML page |
| DevDocs Sync | N/A | `docker logs mcpdocker-devdocs-sync` | Check for successful sync messages |

## Installation Issues

### Docker Installation Problems

#### Issue: Docker not installed or not running
```bash
# Check Docker installation
docker --version
docker compose --version

# Check Docker daemon status (Linux)
sudo systemctl status docker

# Start Docker service (Linux)
sudo systemctl start docker

# Check Docker daemon status (macOS/Windows)
docker info
```

**Solution:**
- Install Docker Desktop from official website
- Ensure Docker daemon is running
- Add user to docker group (Linux): `sudo usermod -aG docker $USER`

#### Issue: Docker compose not found
```bash
# Check Docker Compose version
docker compose version

# Alternative: check legacy docker-compose
docker-compose --version
```

**Solution:**
- Update Docker Desktop to latest version
- Install Docker Compose plugin: `sudo apt-get install docker-compose-plugin`

### Permission Issues

#### Issue: Permission denied accessing Docker socket
```bash
# Error: permission denied while trying to connect to Docker daemon socket
```

**Solution:**
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER
# Logout and login again

# Temporary fix (not recommended for production)
sudo chmod 666 /var/run/docker.sock

# Check current permissions
ls -l /var/run/docker.sock
```

#### Issue: Volume mount permission problems
```bash
# Error: cannot access mounted files in container
```

**Solution:**
```bash
# Set correct ownership for workspace
sudo chown -R $USER:$USER ./workspace

# Use bind mounts with correct user mapping
docker run -u $(id -u):$(id -g) ...
```

## Service Startup Issues

### Port Conflicts

#### Issue: Port already in use
```bash
# Error: bind: address already in use
```

**Diagnosis:**
```bash
# Check what's using the ports
sudo lsof -i :3000
sudo lsof -i :9292
sudo netstat -tulpn | grep :3000
```

**Solution:**
```bash
# Kill process using the port
sudo kill -9 <PID>

# Or change port in compose.yml
services:
  mcpdocker:
    ports:
      - "3001:3000"  # Change host port to 3001
```

### Memory and Resource Issues

#### Issue: Out of memory errors
```bash
# Error: cannot allocate memory
```

**Diagnosis:**
```bash
# Check available memory
free -h
docker system df
docker stats
```

**Solution:**
```bash
# Clean up Docker resources
docker system prune -a
docker volume prune

# Increase swap space (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Add resource limits in compose.yml
services:
  mcpdocker:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

#### Issue: Disk space exhausted
```bash
# Error: no space left on device
```

**Solution:**
```bash
# Clean up Docker images and containers
docker system prune -a --volumes

# Remove unused containers
docker container prune

# Remove unused images
docker image prune -a

# Check disk usage
df -h
du -sh /var/lib/docker
```

## Runtime Issues

### Container Creation Problems

#### Issue: Container fails to start
```bash
# Error: container exits immediately
```

**Diagnosis:**
```bash
# Check container logs
docker logs <container_name>

# Check container status
docker ps -a

# Inspect container configuration
docker inspect <container_name>
```

**Solution:**
```bash
# Run container interactively to debug
docker run -it --rm <image_name> /bin/sh

# Check image exists and is accessible
docker pull <image_name>

# Verify container configuration
# Common issues: wrong entrypoint, missing environment variables
```

#### Issue: Container networking problems
```bash
# Error: cannot connect to container ports
```

**Diagnosis:**
```bash
# Check port mapping
docker port <container_name>

# Check network configuration
docker network ls
docker network inspect mcp-network

# Test internal connectivity
docker exec <container> ping google.com
```

**Solution:**
```bash
# Recreate network
docker network rm mcp-network
docker network create mcp-network

# Check firewall settings
sudo ufw status
sudo iptables -L

# Test port accessibility
telnet localhost 3000
```

### Documentation Service Issues

#### Issue: DevDocs not accessible
```bash
# Error: cannot connect to DevDocs service
```

**Diagnosis:**
```bash
# Check DevDocs container status
docker logs mcpdocker-devdocs

# Test internal connectivity
docker exec mcpdocker-server curl http://devdocs:9292

# Check network connectivity
docker network inspect mcp-network
```

**Solution:**
```bash
# Restart DevDocs service
docker compose restart devdocs

# Check DevDocs configuration
docker exec mcpdocker-devdocs ls -la /devdocs

# Manual DevDocs restart
docker exec mcpdocker-devdocs supervisorctl restart all
```

#### Issue: Documentation not syncing
```bash
# Error: documentation outdated or missing
```

**Diagnosis:**
```bash
# Check sync container logs
docker logs mcpdocker-devdocs-sync

# Check documentation directory
docker exec mcpdocker-devdocs ls -la /devdocs/public/docs
```

**Solution:**
```bash
# Manually trigger sync
docker exec mcpdocker-devdocs-sync python sync_docs.py

# Restart sync service
docker compose restart devdocs-sync

# Check network connectivity for downloads
docker exec mcpdocker-devdocs-sync ping github.com
```

## Performance Issues

### Slow Container Operations

#### Issue: Containers take long time to create/start
```bash
# Containers are slow to respond
```

**Diagnosis:**
```bash
# Check system resources
docker stats
htop
iotop

# Check Docker daemon configuration
docker info | grep -i storage
```

**Solution:**
```bash
# Optimize Docker storage driver
# Edit /etc/docker/daemon.json
{
  "storage-driver": "overlay2",
  "storage-opts": ["overlay2.override_kernel_check=true"]
}

# Restart Docker daemon
sudo systemctl restart docker

# Pre-pull commonly used images
docker pull python:3.11-slim
docker pull node:18-alpine
```

#### Issue: High memory usage
```bash
# System running out of memory
```

**Solution:**
```bash
# Set container memory limits
# In compose.yml or when creating containers
deploy:
  resources:
    limits:
      memory: 512M

# Clean up unused containers regularly
docker container prune

# Monitor memory usage
docker stats --no-stream
```

### Network Performance Issues

#### Issue: Slow network connectivity from containers
```bash
# Network requests are slow or timing out
```

**Diagnosis:**
```bash
# Test DNS resolution
docker exec <container> nslookup google.com

# Test network speed
docker exec <container> curl -w "@curl-format.txt" -o /dev/null -s http://google.com

# Check Docker network configuration
docker network inspect bridge
```

**Solution:**
```bash
# Configure DNS servers
# Edit /etc/docker/daemon.json
{
  "dns": ["8.8.8.8", "8.8.4.4"]
}

# Use host networking for better performance (when safe)
docker run --network host <image>

# Optimize network settings
echo 'net.core.rmem_max = 16777216' >> /etc/sysctl.conf
```

## API and Integration Issues

### Claude Desktop Integration Problems

#### Issue: MCP server not detected by Claude Desktop
```bash
# Claude Desktop doesn't show MCP tools
```

**Diagnosis:**
```bash
# Check Claude Desktop configuration
cat ~/.config/claude-desktop/config.json  # Linux
cat ~/Library/Application\ Support/Claude/config.json  # macOS

# Verify MCP server is running
curl http://localhost:3000/health
```

**Solution:**
```bash
# Update Claude Desktop configuration
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

# Completely restart Claude Desktop
# Kill all Claude processes and restart
```

#### Issue: Authentication failures
```bash
# Error: authentication required or token expired
```

**Solution:**
```bash
# Generate new secret key
openssl rand -hex 32

# Update environment variable
export MCP_SECRET_KEY="new_secret_key_here"

# Restart services
docker compose restart
```

### API Request Failures

#### Issue: API timeouts or connection refused
```bash
# Error: connection timeout or refused
```

**Diagnosis:**
```bash
# Check server status
curl -v http://localhost:3000/health

# Check container logs
docker logs mcpdocker-server

# Verify network connectivity
telnet localhost 3000
```

**Solution:**
```bash
# Increase timeout values
# In environment variables or configuration
REQUEST_TIMEOUT=60
CONTAINER_TIMEOUT=600

# Check firewall rules
sudo ufw status
sudo iptables -L INPUT

# Test with different network interface
docker run -p 127.0.0.1:3000:3000 ...
```

## Browser Automation Issues

### Playwright/Selenium Problems

#### Issue: Browser fails to launch
```bash
# Error: could not launch browser
```

**Diagnosis:**
```bash
# Check if browser binaries are installed
docker exec <container> which chromium-browser
docker exec <container> which firefox

# Check display configuration for headless mode
echo $DISPLAY
```

**Solution:**
```bash
# Install browser dependencies
# Add to Dockerfile or install in container
RUN apt-get update && apt-get install -y \
    chromium-browser \
    firefox-esr \
    xvfb

# Use headless mode
browser = await playwright_launch_browser(headless=True)

# Set up virtual display
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x24 &
```

#### Issue: Screenshot capture fails
```bash
# Error: could not capture screenshot
```

**Solution:**
```bash
# Ensure proper permissions for file writes
docker exec <container> ls -la /workspace

# Use proper screenshot parameters
await playwright_screenshot(
    page_id=page.id,
    filename="screenshot.png",
    full_page=False  # Try with full_page=False first
)
```

## Database and Storage Issues

### Volume Mount Problems

#### Issue: Data not persisting between container restarts
```bash
# Data is lost when container restarts
```

**Solution:**
```bash
# Check volume configuration
docker volume ls
docker volume inspect mcp-workspace

# Ensure proper volume mounting in compose.yml
volumes:
  - mcp-workspace:/workspace
  - ./data:/app/data  # For host bind mount

# Set correct file permissions
sudo chown -R 1000:1000 ./data
```

#### Issue: Database connection failures
```bash
# Error: could not connect to database
```

**Diagnosis:**
```bash
# Check database container status
docker logs <db_container>

# Test database connectivity
docker exec <app_container> ping <db_container>

# Check database is listening on correct port
docker exec <db_container> netstat -tlnp
```

**Solution:**
```bash
# Wait for database to be ready
# Add health check or wait script
while ! nc -z database 5432; do sleep 1; done

# Use correct connection parameters
DATABASE_URL=postgresql://user:password@database:5432/dbname
```

## Security and Access Issues

### Permission Denied Errors

#### Issue: Cannot access files or execute commands
```bash
# Error: permission denied
```

**Solution:**
```bash
# Run container with correct user mapping
docker run -u $(id -u):$(id -g) ...

# Set proper file permissions
chmod +x script.sh
chown user:group file.txt

# Use sudo in container when necessary
docker exec -u root <container> chown user:group /path
```

### Security Policy Violations

#### Issue: Security level too restrictive
```bash
# Error: operation not allowed by security policy
```

**Solution:**
```bash
# Adjust security level in configuration
SECURITY_LEVEL=LOW  # For development
SECURITY_LEVEL=MEDIUM  # For testing  
SECURITY_LEVEL=HIGH  # For production

# Review and adjust specific security policies
# Check configuration.json and compose.yml
```

## Monitoring and Logging

### Log Analysis

#### Viewing and analyzing logs effectively:
```bash
# View recent logs
docker compose logs --tail=100

# Follow logs in real-time
docker compose logs -f

# View logs for specific service
docker compose logs mcpdocker

# Search logs for errors
docker compose logs | grep -i error
docker compose logs | grep -i "failed\|exception\|traceback"

# Export logs for analysis
docker compose logs > mcp_logs.txt
```

### Performance Monitoring

#### Monitor system resources:
```bash
# Container resource usage
docker stats

# System resource usage
htop
iotop
nethogs

# Docker system information
docker system df
docker system info
```

## Recovery Procedures

### Complete System Reset

When all else fails, perform a complete reset:

```bash
# 1. Stop all services
docker compose down

# 2. Remove all containers and networks
docker container prune -f
docker network prune -f

# 3. Clean up images and volumes (careful - removes data!)
docker system prune -a --volumes

# 4. Remove and recreate workspace
docker volume rm mcp-workspace
docker volume create mcp-workspace

# 5. Restart services
docker compose up -d --build

# 6. Verify everything is working
docker compose ps
curl http://localhost:3000/health
```

### Backup and Restore

#### Create backup:
```bash
# Backup workspace volume
docker run --rm -v mcp-workspace:/source -v $(pwd):/backup alpine \
  tar -czf /backup/mcp-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /source .

# Backup configuration
cp -r . ./mcp-backup-config/
```

#### Restore from backup:
```bash
# Restore workspace volume
docker run --rm -v mcp-workspace:/target -v $(pwd):/backup alpine \
  tar -xzf /backup/mcp-backup-YYYYMMDD-HHMMSS.tar.gz -C /target

# Restore configuration
cp -r ./mcp-backup-config/* .
```

## Getting Help

### Collecting Debug Information

When reporting issues, collect this information:

```bash
# System information
echo "=== System Info ===" > debug_info.txt
uname -a >> debug_info.txt
docker --version >> debug_info.txt
docker compose version >> debug_info.txt

# Docker system info
echo -e "\n=== Docker System Info ===" >> debug_info.txt
docker system info >> debug_info.txt

# Container status
echo -e "\n=== Container Status ===" >> debug_info.txt
docker compose ps >> debug_info.txt

# Recent logs
echo -e "\n=== Recent Logs ===" >> debug_info.txt
docker compose logs --tail=100 >> debug_info.txt

# Network information
echo -e "\n=== Network Info ===" >> debug_info.txt
docker network ls >> debug_info.txt
docker network inspect mcp-network >> debug_info.txt

# Resource usage
echo -e "\n=== Resource Usage ===" >> debug_info.txt
docker stats --no-stream >> debug_info.txt
```

### Support Resources

- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check [main documentation](../main.md) for detailed guides
- **Community**: Join discussions and get help from other users
- **Logs**: Always include relevant logs when seeking help

### Common Resolution Steps

1. **Check the basics**: Ensure Docker is running, ports are available, sufficient resources
2. **Review logs**: Look for error messages in container logs
3. **Test connectivity**: Verify network connectivity between services
4. **Clean and restart**: Clean up Docker resources and restart services
5. **Update**: Ensure you're using the latest version
6. **Reset if necessary**: Perform a complete reset as last resort

This troubleshooting guide covers the most common issues and their solutions. For persistent problems, collect debug information and seek help through the appropriate support channels.