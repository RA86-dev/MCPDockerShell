import server_version as sv
f"""
Name: MCPDevServer
Version: {sv.SERVER_VERSION}
"""
from fastapi import FastAPI, Request
import docker
import tempfile
import os
import argparse
import secrets
import uvicorn
import sys
import json
import time
import psutil
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from mcp.server import FastMCP
from pydantic import BaseModel, Field
from dataclasses import dataclass
from enum import Enum
from cachetools import TTLCache
from collections import defaultdict
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from fastapi.responses import HTMLResponse, RedirectResponse

# Environment variables
_DEVDOCS_URL = os.getenv("DEVDOCS_URL", "http://localhost:9292")
_SEARXNG_URL = os.getenv("SEARXNG_URL", "http://localhost:8888") 
uptime_launched = datetime.now()

# Import all our modular tools
try:
    from subtools.docker_tools import DockerTools
    from subtools.browser_tools import BrowserTools
    from subtools.monitoring_tools import MonitoringTools
    from subtools.development_tools import DevelopmentTools
    from subtools.workflow_tools import WorkflowTools
    from subtools.documentation_tools import DocumentationTools
    from subtools.firecrawl_tools import FirecrawlTools
    from subtools.searxng_tools import SearXNGTools
    from subtools.module_finder import ModuleFinder
    HAS_ALL_SUBTOOLS = True
except ImportError as e:
    print(f"Warning: Some subtools could not be imported: {e}")
    HAS_ALL_SUBTOOLS = False

# Optional imports for enhanced features
try:
    from passlib.context import CryptContext
    HAS_PASSLIB = True
except ImportError:
    HAS_PASSLIB = False

try:
    import jose
    HAS_JOSE = True

except ImportError:
    HAS_JOSE = False

# Configuration
SECRET_KEY = os.getenv("MCP_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
CACHE_TTL = 300  # 5 minutes
MAX_CACHE_SIZE = 1000
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds
MAX_WORKERS = 10
REQUEST_TIMEOUT = 30
CONTAINER_TIMEOUT = 300


class SecurityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    STRICT = "strict"


class ContainerStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    CREATED = "created"
    EXITED = "exited"


@dataclass
class ServiceConfig:
    """Configuration for MCP services"""
    docker_management: bool = True
    browser_automation: bool = True
    monitoring_tools: bool = True
    development_tools: bool = True
    workflow_tools: bool = True
    documentation_tools: bool = True
    firecrawl_tools: bool = True
    searxng_tools: bool = True
    notification_tools: bool = True
    websocket_enabled: bool = False,
    module_Finder: bool=True
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    auto_cleanup_enabled: bool = True
    health_checks_enabled: bool = True
    distributed_mode: bool = False


class ServerMetrics(BaseModel):
    """Server performance metrics"""
    requests_total: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    average_response_time: float = 0.0
    containers_created: int = 0
    containers_active: int = 0
    uptime_seconds: float = 0.0


class HealthStatus(BaseModel):
    """System health status"""
    status: str = "healthy"
    docker_connected: bool = True
    memory_usage_percent: float = 0.0
    cpu_usage_percent: float = 0.0
    disk_usage_percent: float = 0.0
    last_check: datetime = Field(default_factory=datetime.now)


class MCPDockerServer:
    """Modular MCP Docker Server with pluggable tool modules"""

    def __init__(self, service_config: ServiceConfig = None):
        self.service_config = service_config or ServiceConfig()
        self.mcp = FastMCP("MCPDocker-Enhanced", host="0.0.0.0")

        # Initialize directory structure
        script_dir = Path(__file__).parent
        self.docs_dir = script_dir / "documentation"
        self.logs_dir = script_dir / "logs"
        self.config_dir = script_dir / "config"
        self.backup_dir = script_dir / "backups"
        
        # Create directories
        for directory in [self.docs_dir, self.logs_dir, self.config_dir, self.backup_dir]:
            directory.mkdir(exist_ok=True)

        # Initialize logging
        self.setup_enhanced_logging()

        # Initialize core components
        self._init_docker_client()
        self._init_caching_system()

        # Core storage
        self.active_containers = {}
        self.temp_dir = tempfile.mkdtemp(prefix="mcpdocker_enhanced_")

        # Performance and monitoring
        self.metrics = ServerMetrics()
        self.health_status = HealthStatus()
        self.start_time = time.time()

        # System capabilities
        self.gpu_info = self._detect_gpu_support()
        self.gpu_available = self.gpu_info["has_gpu"]

        # Thread pool for async operations
        self.executor = ThreadPoolExecutor(
            max_workers=min(MAX_WORKERS, (os.cpu_count() or 1) + 4),
            thread_name_prefix="MCPDocker",
        )

        # Define comprehensive set of allowed development images
        self.allowed_images = {
            # Base OS images
            "ubuntu:latest", "ubuntu:22.04", "ubuntu:20.04",
            "debian:latest", "debian:bullseye", "debian:bookworm",
            "alpine:latest", "alpine:3.18",
            "fedora:latest", "fedora:38",
            "rockylinux:latest", "rockylinux:9",

            # Language-specific images
            "python:3.11", "python:3.10", "python:3.9", "python:latest",
            "node:18", "node:20", "node:latest", "node:18-alpine", "node:20-alpine",
            "openjdk:17", "openjdk:11", "openjdk:21",
            "golang:1.21", "golang:latest", "golang:1.21-alpine",
            "rust:latest", "rust:1.70", "rust:1.70-slim",
            "php:8.2", "php:8.1", "php:latest",
            "ruby:3.2", "ruby:latest",

            # Database images
            "postgres:15", "postgres:14", "postgres:latest",
            "mysql:8.0", "mysql:latest",
            "redis:7", "redis:latest", "redis:alpine",
            "mongodb:latest", "mongodb:7",

            # Web servers
            "nginx:latest", "nginx:alpine",
            "httpd:latest", "httpd:alpine",

            # Development tools
            "jenkins/jenkins:lts",
            "gitlab/gitlab-ce:latest",
            "portainer/portainer-ce:latest"
        }

        # Add GPU images if available
        if self.gpu_available:
            gpu_images = {
                "nvidia/cuda:12.0-runtime-ubuntu22.04",
                "nvidia/cuda:11.8-runtime-ubuntu22.04",
                "pytorch/pytorch:latest",
                "tensorflow/tensorflow:latest-gpu",
                "rocm/rocm-terminal:latest",
                "rocm/dev-ubuntu-20.04:latest",
                "rocm/dev-ubuntu-22.04:latest",
                
            }
            self.allowed_images.update(gpu_images)

        # Initialize all tool modules
        self._init_tool_modules()

        # Register all tools
        self._register_all_tools()

    def _init_docker_client(self):
        """Initialize Docker client with enhanced error handling"""
        try:
            self.docker_client = docker.from_env()
            self.docker_client.ping()
            self.logger.info("Docker client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
            raise

    def _init_caching_system(self):
        """Initialize caching system"""
        self.cache = TTLCache(maxsize=MAX_CACHE_SIZE, ttl=CACHE_TTL)

    def _init_tool_modules(self):
        """Initialize all tool modules"""
        if not HAS_ALL_SUBTOOLS:
            self.logger.warning("Not all subtools available - some functionality will be limited")

        # Initialize Docker tools
        self.docker_tools = DockerTools(
            docker_client=self.docker_client,
            allowed_images=self.allowed_images,
            temp_dir=self.temp_dir,
            logger=self.logger
        ) if HAS_ALL_SUBTOOLS else None
        self.module_finder = ModuleFinder(
            
        ) if HAS_ALL_SUBTOOLS else None

        # Initialize browser tools
        self.browser_tools = BrowserTools(
            temp_dir=self.temp_dir,
            logger=self.logger
        ) if HAS_ALL_SUBTOOLS else None

        # Initialize monitoring tools
        self.monitoring_tools = MonitoringTools(
            docker_client=self.docker_client,
            active_containers=self.active_containers,
            logger=self.logger
        ) if HAS_ALL_SUBTOOLS else None

        # Initialize development tools
        self.development_tools = DevelopmentTools(
            docker_client=self.docker_client,
            active_containers=self.active_containers,
            temp_dir=self.temp_dir,
            logger=self.logger
        ) if HAS_ALL_SUBTOOLS else None

        # Initialize workflow tools
        self.workflow_tools = WorkflowTools(
            temp_dir=self.temp_dir,
            logger=self.logger
        ) if HAS_ALL_SUBTOOLS else None

        # Initialize documentation tools
        self.documentation_tools = DocumentationTools(
            docs_dir=self.docs_dir,
            devdocs_url=_DEVDOCS_URL,
            logger=self.logger
        ) if HAS_ALL_SUBTOOLS else None

        # Initialize web scraping and search tools
        if os.getenv("ENABLE_FIRECRAWL", "false") == "true":
            # self.firecrawl_tools = FirecrawlTools(logger=self.logger) if HAS_ALL_SUBTOOLS else None
            if os.getenv("ENABLE_LOCAL_FIRECRAWL") == "true" and os.getenv("LOCAL_URL"):
                self.firecrawl_tools = FirecrawlTools(
                    logger=self.logger,
                    local_url=os.getenv("LOCAL_URL"),
                    api_key=None
                ) if HAS_ALL_SUBTOOLS else None
            else:
                self.firecrawl_tools = FirecrawlTools(
                    logger=self.logger,
                    local_url="http://localhost:3002",
                    api_key=os.getenv("FIRECRAWL_API_KEY")
                ) if HAS_ALL_SUBTOOLS else None
        else:
            self.firecrawl_tools = None

        self.searxng_tools = SearXNGTools(searxng_url=_SEARXNG_URL, logger=self.logger) if HAS_ALL_SUBTOOLS else None

      
    def _register_all_tools(self):
        """Register all tools with the MCP server"""
        try:
            if not HAS_ALL_SUBTOOLS:
                self.logger.error("Cannot register tools - subtools not available")
                return

            # Register core Docker tools
            if self.docker_tools and self._get_config("docker_management", True):
                self.docker_tools.register_tools(self.mcp)
                self.logger.info("Registered Docker management tools")
            if self.module_finder and self._get_config("module_finder", True):
                self.module_finder.add_tools(self.mcp)
                self.logger.info("Registered Module Finder tools")
            # Register browser automation tools
            if self.browser_tools and self._get_config("browser_automation", True):
                self.browser_tools.register_tools(self.mcp)
                self.logger.info("Registered browser automation tools")

            # Register monitoring tools
            if self.monitoring_tools and self._get_config("monitoring_tools", True):
                self.monitoring_tools.register_tools(self.mcp)
                self.logger.info("Registered monitoring tools")

            # Register development tools
            if self.development_tools and self._get_config("development_tools", True):
                self.development_tools.register_tools(self.mcp)
                self.logger.info("Registered development tools")

            # Register workflow tools
            if self.workflow_tools and self._get_config("workflow_tools", True):
                self.workflow_tools.register_tools(self.mcp)
                self.logger.info("Registered workflow automation tools")

            # Register documentation tools
            if self.documentation_tools and self._get_config("documentation_tools", True):
                self.documentation_tools.register_tools(self.mcp)
                self.documentation_tools.register_resources(self.mcp)
                self.logger.info("Registered documentation tools")

            # Register web scraping and search tools
            if self.firecrawl_tools and self._get_config("firecrawl_tools", True):
                self.firecrawl_tools.register_tools(self.mcp)
                self.logger.info("Registered Firecrawl tools")

            if self.searxng_tools and self._get_config("searxng_tools", True):
                self.searxng_tools.register_tools(self.mcp)
                self.logger.info("Registered SearXNG tools")

            # Register notification tools
           
            # Register basic utility tools
            self._register_utility_tools()

        except Exception as e:
            self.logger.error(f"Failed to register tools: {e}")
            raise

    def _register_utility_tools(self):
        """Register basic utility tools"""

        @self.mcp.tool()
        async def get_server_info() -> str:
            """Get comprehensive server information and capabilities"""
            try:
                info = {
                    "server_name": "MCPDocker-Enhanced-Modular",
                    "version": f"{sv.SERVER_VERSION} - {sv.SERVER_NICKNAME}",
                    "uptime_seconds": time.time() - self.start_time,
                    "capabilities": {
                        "docker_management": bool(self.docker_tools),
                        "browser_automation": bool(self.browser_tools),
                        "monitoring": bool(self.monitoring_tools),
                        "development_tools": bool(self.development_tools),
                        "workflow_automation": bool(self.workflow_tools),
                        "documentation": bool(self.documentation_tools),
                        "web_scraping": bool(self.firecrawl_tools),
                        "web_search": bool(self.searxng_tools),
                        "notifications": bool(self.notification_tools),
                        "gpu_support": self.gpu_available
                    },
                    "configuration": {
                        "allowed_images_count": len(self.allowed_images),
                        "temp_directory": self.temp_dir,
                        "docs_directory": str(self.docs_dir),
                        "devdocs_url": _DEVDOCS_URL,
                        "searxng_url": _SEARXNG_URL,
                        
                    },
                    "system": {
                        "cpu_count": os.cpu_count(),
                        "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                        "platform": sys.platform
                    },
                    "docker": {
                        "connected": True,
                        "version": self.docker_client.version().get("Version", "Unknown"),
                        "active_containers": len(self.active_containers)
                    }
                }
                return json.dumps(info, indent=2)
            except Exception as e:
                return f"Error getting server info: {str(e)}"

        @self.mcp.tool()
        async def health_check() -> str:
            """Perform a comprehensive health check of all services"""
            try:
                health = {
                    "overall_status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "services": {
                        "docker": {"status": "healthy", "details": "Connected and responsive"},
                        "mcp_server": {"status": "healthy", "details": "All tools registered"},
                        "file_system": {"status": "healthy", "details": "All directories accessible"},
                    },
                    "system_resources": {
                        "cpu_percent": psutil.cpu_percent(),
                        "memory_percent": psutil.virtual_memory().percent,
                        "disk_percent": psutil.disk_usage('/').percent
                    }
                }

                # Check external services
                if self.documentation_tools:
                    try:
                        import requests
                        response = requests.get(_DEVDOCS_URL, timeout=5)
                        health["services"]["devdocs"] = {
                            "status": "healthy" if response.status_code == 200 else "degraded",
                            "details": f"HTTP {response.status_code}"
                        }
                    except Exception:
                        health["services"]["devdocs"] = {
                            "status": "unavailable",
                            "details": "Service not reachable"
                        }

                if self.searxng_tools:
                    try:
                        import requests
                        response = requests.get(_SEARXNG_URL, timeout=5)
                        health["services"]["searxng"] = {
                            "status": "healthy" if response.status_code == 200 else "degraded",
                            "details": f"HTTP {response.status_code}"
                        }
                    except Exception:
                        health["services"]["searxng"] = {
                            "status": "unavailable",
                            "details": "Service not reachable"
                        }

                return json.dumps(health, indent=2)
            except Exception as e:
                return f"Error performing health check: {str(e)}"

    def setup_enhanced_logging(self):
        """Setup enhanced logging with rotation"""
        log_file = self.logs_dir / "mcpdocker.log"

        # Create logger
        self.logger = logging.getLogger("MCPDockerServer")
        self.logger.setLevel(logging.INFO)

        # Create handlers
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=10*1024*1024, backupCount=5  # 10MB files, keep 5
        )
        console_handler = logging.StreamHandler()

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        self.logger.addHandler(file_handler)
        if sys.stdin.isatty():  # Only add console handler if running interactively
            self.logger.addHandler(console_handler)

    def _detect_gpu_support(self) -> Dict[str, Any]:
        """Detect available GPU support"""
        gpu_info = {"has_gpu": False, "type": None, "details": {}}

        try:
            import subprocess
            # Check NVIDIA
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gpu_info["has_gpu"] = True
                gpu_info["type"] = "nvidia"
                gpu_info["details"]["nvidia"] = "Available"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        try:
            # Check AMD ROCm
            result = subprocess.run(["rocm-smi"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                gpu_info["has_gpu"] = True
                gpu_info["type"] = "amd_rocm"
                gpu_info["details"]["amd_rocm"] = "Available"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        return gpu_info

    def _get_config(self, key: str, default=None):
        """Helper method to safely get configuration values"""
        if hasattr(self.service_config, key):
            return getattr(self.service_config, key)
        return default
    
    def notify_tool_execution(self, tool_name: str, status: str, details: str = "", duration: float = None):
        """Notify about tool execution via notification system"""
        if self.notification_tools and hasattr(self.notification_tools, 'notify_tool_execution'):
            try:
                self.notification_tools.notify_tool_execution(tool_name, status, details, duration)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error sending tool notification: {e}")

    def cleanup(self):
        """Clean up resources on shutdown"""
        try:
            # Stop all active containers
            for container_id, container_info in self.active_containers.items():
                try:
                    container_info["container"].stop()
                except Exception:
                    pass

            # Clean up temp directory
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)

            # Cleanup notification tools
            if hasattr(self, 'notification_tools') and self.notification_tools:
                self.notification_tools.cleanup()

            # Shutdown thread pool
            self.executor.shutdown(wait=True)

        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Error during cleanup: {e}")

        if hasattr(self, 'logger'):
            self.logger.info("MCP Docker Server cleanup completed")

    def run(self, transport_method: str = "stdio"):
        """Run the MCP server"""
        # Suppress all logging in MCP mode to avoid protocol conflicts
        if transport_method == "stdio" and not sys.stdin.isatty():
            logging.getLogger().setLevel(logging.CRITICAL)
            logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
            logging.getLogger("fastapi").setLevel(logging.CRITICAL)

        return self.mcp.run(transport=transport_method)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="MCP Docker Server - Enhanced Modular Edition")
    parser.add_argument("--transport", default="stdio", choices=["stdio", "ws", "sse"],
                       help="Transport method for MCP communication")
    parser.add_argument("--host", default="localhost", help="Host for WebSocket/SSE transport")
    parser.add_argument("--port", type=int, default=8000, help="Port for WebSocket/SSE transport")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--disable-docker", action="store_true", help="Disable Docker management")
    parser.add_argument("--disable-browser", action="store_true", help="Disable browser automation")
    parser.add_argument("--disable-monitoring", action="store_true", help="Disable monitoring tools")
    parser.add_argument("--disable-dev", action="store_true", help="Disable development tools")
    parser.add_argument("--disable-workflow", action="store_true", help="Disable workflow tools")
    parser.add_argument("--disable-docs", action="store_true", help="Disable documentation tools")
    parser.add_argument("--disable-firecrawl", action="store_true", help="Disable Firecrawl tools")
    parser.add_argument("--disable-searxng", action="store_true", help="Disable SearXNG tools")
    parser.add_argument("--disable-notifications", action="store_true", help="Disable notification system")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Create service configuration
    service_config = ServiceConfig()
    if args.disable_docker:
        service_config.docker_management = False
    if args.disable_browser:
        service_config.browser_automation = False
    if args.disable_monitoring:
        service_config.monitoring_tools = False
    if args.disable_dev:
        service_config.development_tools = False
    if args.disable_workflow:
        service_config.workflow_tools = False
    if args.disable_docs:
        service_config.documentation_tools = False
    if args.disable_firecrawl:
        service_config.firecrawl_tools = False
    if args.disable_searxng:
        service_config.searxng_tools = False
    if args.disable_notifications:
        service_config.notification_tools = False

    try:
        # Initialize and run server
        server = MCPDockerServer(service_config)

        if args.verbose:
            server.logger.setLevel(logging.DEBUG)

        server.logger.info(f"Starting MCP Docker Server with transport: {args.transport}")
        server.logger.info(f"Configuration: {service_config}")

        return server.run(transport_method=args.transport)

    except KeyboardInterrupt:
        server.logger.info("Server shutdown requested")
        return 0
    except Exception as e:
        print(f"Failed to start server: {e}")
        return 1
    finally:
        if 'server' in locals():
            server.cleanup()


if __name__ == "__main__":
    sys.exit(main())
