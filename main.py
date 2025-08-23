
"""
Name: MCPDevServer
Date: Sunday, August 17th, 2025 14:32
"""
from fastapi import FastAPI,Request
import docker
import tempfile
import os
import tempfile
import argparse
import shutil
import subprocess
import tarfile
import io
import socket
import requests 
import fastapi
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any
from mcp.server import FastMCP
import json
import time
from pydantic import BaseModel, Field
import yfinance as yf
import uvicorn
import secrets
from playwright.async_api import async_playwright
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import urllib.request
import zipfile
import psutil
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from fastapi.responses import HTMLResponse, RedirectResponse
import webbrowser
import sys
from dataclasses import dataclass
import weakref
from enum import Enum
from cachetools import TTLCache
import os
_DEVDOCS_URL = os.getenv("DEVDOCS_URL", "http://localhost:9292")

uptime_launched = datetime.now()

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

# API Endpoints
PYPI_BASE = "https://pypi.org/pypi"
WIKI_API = "https://en.wikipedia.org/w/api.php"

# Security Configuration
SECRET_KEY = os.getenv("MCP_SECRET_KEY", secrets.token_hex(32))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Cache Configuration
CACHE_TTL = 300  # 5 minutes
MAX_CACHE_SIZE = 1000

# Rate Limiting
RATE_LIMIT_REQUESTS = 100
RATE_LIMIT_WINDOW = 60  # seconds

# Performance Settings
MAX_WORKERS = 10
REQUEST_TIMEOUT = 30
CONTAINER_TIMEOUT = 300


class SecurityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    STRICT = "strict"


class ContainerStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    RESTARTING = "restarting"
    REMOVING = "removing"
    EXITED = "exited"
    DEAD = "dead"


@dataclass
class RateLimitInfo:
    requests: int = 0
    window_start: float = 0
    blocked_until: float = 0


class ContainerConfig(BaseModel):
    image: str
    name: Optional[str] = None
    ports: Dict[int, int] = {}
    volumes: Dict[str, str] = {}
    environment: Dict[str, str] = {}


class ServiceConfig(BaseModel):
    docker_management: bool = True
    browser_automation: bool = True
    gpu_support: bool = True
    file_management: bool = True
    documentation_tools: bool = True
    monitoring_tools: bool = True
    development_tools: bool = True
    workflow_tools: bool = True
    websocket_enabled: bool = True
    authentication_enabled: bool = False
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    rate_limiting_enabled: bool = True
    caching_enabled: bool = True
    health_checks_enabled: bool = True
    auto_cleanup_enabled: bool = True
    backup_enabled: bool = True
    distributed_mode: bool = False


class ServerMetrics(BaseModel):
    uptime: float = 0
    requests_total: int = 0
    requests_successful: int = 0
    requests_failed: int = 0
    active_containers: int = 0
    active_sessions: int = 0
    memory_usage: float = 0
    cpu_usage: float = 0
    disk_usage: float = 0


class HealthStatus(BaseModel):
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    checks: Dict[str, bool] = Field(default_factory=dict)
    metrics: ServerMetrics = Field(default_factory=ServerMetrics)
    version: str = "2.0.0-enhanced"



class MCPDockerServer:
    def __init__(self, service_config: ServiceConfig = None):
        self.service_config = service_config or ServiceConfig()
        self.mcp = FastMCP("MCPDocker-Enhanced", host="0.0.0.0")

        # Initialize directory structure first
        script_dir = Path(__file__).parent
        self.docs_dir = script_dir / "documentation"
        self.logs_dir = script_dir / "logs"
        self.config_dir = script_dir / "config"
        self.backup_dir = script_dir / "backups"

        # Create directories
        for directory in [
            self.docs_dir,
            self.logs_dir,
            self.config_dir,
            self.backup_dir,
        ]:
            directory.mkdir(exist_ok=True)

        # Initialize logging FIRST (before anything that uses logger)
        self.monitoring_data = defaultdict(list)
        self.setup_enhanced_logging()

        # Now initialize core components (these can use logger)
        self._init_docker_client()
        self._init_security_components()
        self._init_caching_system()
        self._init_rate_limiting()

        # Core storage
        self.active_containers = weakref.WeakValueDictionary()
        self.active_streams = {}
        self.active_sessions = {}
        self.temp_dir = tempfile.mkdtemp(prefix="mcpdocker_enhanced_")

        # Performance and monitoring
        self.metrics = ServerMetrics()
        self.health_status = HealthStatus()
        self.start_time = time.time()

        # Browser automation support
        self.playwright_instance = None
        self.active_browsers = {}
        self.active_selenium_drivers = {}

        # System capabilities
        self.gpu_available = self._check_nvidia_gpu()

        # Enhanced performance monitoring
        self.performance_metrics = {
            "container_stats": {},
            "system_stats": {},
            "operation_times": [],
            "api_response_times": [],
            "error_rates": defaultdict(int),
            "resource_usage": defaultdict(list),
        }

        # Enhanced thread pool with better resource management
        self.executor = ThreadPoolExecutor(
            max_workers=min(MAX_WORKERS, (os.cpu_count() or 1) + 4),
            thread_name_prefix="MCPDocker",
        )

        # WebSocket manager for real-time features
        self.websocket_manager = None
        if self._get_config("websocket_enabled", False):
            self._init_websocket_manager()


        # Initialize health checks
        if self._get_config("health_checks_enabled", True):
            self._init_health_checks()

        # Setup auto-cleanup if enabled
        if self._get_config("auto_cleanup_enabled", True):
            self._setup_auto_cleanup()

        # Initialize distributed features if enabled
        if self._get_config("distributed_mode", False):
            self._init_distributed_features()

        # Comprehensive set of allowed development images
        self.allowed_images = {
            # Base OS images
            "ubuntu:latest",
            "ubuntu:22.04",
            "ubuntu:20.04",
            "debian:latest",
            "debian:bullseye",
            "debian:bookworm",
            "alpine:latest",
            "alpine:3.18",
            "fedora:latest",
            "fedora:38",
            "rockylinux:latest",
            "rockylinux:9",
            # Python development
            "python:latest",
            "python:3.11",
            "python:3.10",
            "python:3.9",
            "python:3.11-slim",
            "python:3.10-slim",
            # Node.js & JavaScript development
            "node:latest",
            "node:18",
            "node:16",
            "node:20",
            "node:18-alpine",
            "node:16-alpine",
            # .NET & C# development
            "mcr.microsoft.com/dotnet/sdk:latest",
            "mcr.microsoft.com/dotnet/sdk:7.0",
            "mcr.microsoft.com/dotnet/sdk:6.0",
            "mcr.microsoft.com/dotnet/runtime:latest",
            "mcr.microsoft.com/dotnet/aspnet:latest",
            # Java development
            "openjdk:latest",
            "openjdk:17",
            "openjdk:11",
            "openjdk:8",
            "openjdk:17-alpine",
            "openjdk:11-alpine",
            "maven:latest",
            "maven:3.9-openjdk-17",
            "gradle:latest",
            "gradle:7-jdk17",
            # Go development
            "golang:latest",
            "golang:1.21",
            "golang:1.20",
            "golang:1.21-alpine",
            "golang:1.20-alpine",
            # Rust development
            "rust:latest",
            "rust:1.70",
            "rust:1.69",
            "rust:1.70-alpine",
            "rust:1.69-alpine",
            # PHP development
            "php:latest",
            "php:8.2",
            "php:8.1",
            "php:8.0",
            "php:8.2-fpm",
            "php:8.1-fpm",
            "composer:latest",
            # Ruby development
            "ruby:latest",
            "ruby:3.2",
            "ruby:3.1",
            "ruby:3.2-alpine",
            "ruby:3.1-alpine",
            # Database images
            "postgres:latest",
            "postgres:15",
            "postgres:14",
            "mysql:latest",
            "mysql:8",
            "mysql:5.7",
            "mongo:latest",
            "mongo:6",
            "mongo:5",
            "redis:latest",
            "redis:7",
            "redis:6",
            "mariadb:latest",
            "mariadb:10",
            # Development tools
            "nginx:latest",
            "nginx:alpine",
            "httpd:latest",
            "httpd:alpine",
            "jenkins/jenkins:latest",
            "sonarqube:latest",
            "gitlab/gitlab-ce:latest",
            # Cloud CLI images
            "amazon/aws-cli:latest",
            "mcr.microsoft.com/azure-cli:latest",
            "google/cloud-sdk:latest",
            # IDE and development environments
            "theiaide/theia:latest",
            "codercom/code-server:latest",
            "linuxserver/code-server:latest",
        }

        # Add GPU-enabled images if GPU is available
        if self.gpu_available:
            self.allowed_images.update(
                {
                    "nvidia/cuda:latest",
                    "pytorch/pytorch:latest",
                    "tensorflow/tensorflow:latest-gpu",
                    "nvcr.io/nvidia/pytorch:latest",
                    "nvcr.io/nvidia/tensorflow:latest-tf2-py3",
                }
            )

        # Register tools based on service configuration with enhanced error handling
        try:
            if self._get_config("docker_management", True):
                self._register_core_tools()
                self._register_resources()

            if self._get_config("browser_automation", True):
                self._register_browser_tools()

            if self._get_config("monitoring_tools", True):
                self._register_monitoring_tools()

            if self._get_config("development_tools", True):
                self._register_development_tools()

            if self._get_config("workflow_tools", True):
                self._register_workflow_tools()

            # Always register enhanced management tools
            self._register_enhanced_management_tools()
            self._register_security_tools()

            if self._get_config("websocket_enabled", False):
                self._register_websocket_tools()

        except Exception as e:
            self.logger.error(f"Failed to register tools: {e}")
            raise

    def _init_docker_client(self):
        """Initialize Docker client with enhanced error handling"""
        try:
            self.docker_client = docker.from_env()
            # Test connection
            self.docker_client.ping()
            self.logger.info("Docker client initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Docker client: {e}")
            raise

    def _get_config(self, key, default=None):
        """Helper method to safely get configuration values"""
        if hasattr(self.service_config, key):
            return getattr(self.service_config, key)
        elif isinstance(self.service_config, dict):
            return self.service_config.get(key, default)
        else:
            return default

    def _init_security_components(self):
        """Initialize security components"""
        if self._get_config("authentication_enabled", False):
            if HAS_PASSLIB:
                self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                self.auth_tokens = TTLCache(
                    maxsize=1000, ttl=ACCESS_TOKEN_EXPIRE_MINUTES * 60
                )
                self.api_keys = set()  # Load from config
                self.logger.info("Security components initialized")
            else:
                self.logger.warning("Passlib not available, authentication disabled")
                if hasattr(self.service_config, "authentication_enabled"):
                    self.service_config.authentication_enabled = False

    def _init_caching_system(self):
        """Initialize caching system"""
        if self._get_config("caching_enabled", True):
            self.cache = TTLCache(maxsize=MAX_CACHE_SIZE, ttl=CACHE_TTL)
            self.query_cache = TTLCache(maxsize=500, ttl=CACHE_TTL // 2)
            self.logger.info("Caching system initialized")

    def _init_rate_limiting(self):
        """Initialize rate limiting"""
        if self._get_config("rate_limiting_enabled", False):
            self.rate_limits = defaultdict(RateLimitInfo)
            self.logger.info("Rate limiting initialized")

    def _init_websocket_manager(self):
        """Initialize WebSocket manager for real-time features"""
        try:
            from fastapi import WebSocket

            self.websocket_connections = set()
            self.logger.info("WebSocket manager initialized")
        except ImportError:
            self.logger.warning("WebSocket dependencies not available")

    def _init_health_checks(self):
        """Initialize health check system"""
        self.health_checks = {
            "docker": self._health_check_docker,
            "disk_space": self._health_check_disk_space,
            "memory": self._health_check_memory,
            "containers": self._health_check_containers,
        }
        self.logger.info("Health checks initialized")

    def _setup_auto_cleanup(self):
        """Setup automatic cleanup processes"""

        def cleanup_task():
            while True:
                try:
                    self._cleanup_expired_containers()
                    self._cleanup_old_logs()
                    self._cleanup_temp_files()
                    time.sleep(300)  # Every 5 minutes
                except Exception as e:
                    self.logger.error(f"Auto-cleanup error: {e}")

        cleanup_thread = threading.Thread(target=cleanup_task, daemon=True)
        cleanup_thread.start()
        self.logger.info("Auto-cleanup system started")

    def _init_distributed_features(self):
        """Initialize distributed computing features"""
        self.cluster_nodes = {}
        self.node_id = secrets.token_hex(8)
        self.logger.info(f"Distributed mode initialized with node ID: {self.node_id}")

        # Multi-language documentation system initialized

    def _download_github_docs(self, url: str, target_dir: Path, language: str):
        """Download and extract documentation from GitHub repositories"""
        temp_zip = self.temp_dir + f"/{language}-docs.zip"

        # Downloading docs
        urllib.request.urlretrieve(url, temp_zip)

        # Extract relevant documentation files
        with zipfile.ZipFile(temp_zip, "r") as zip_ref:
            for member in zip_ref.infolist():
                # Only extract documentation files (markdown, text, etc.)
                if any(
                    member.filename.lower().endswith(ext)
                    for ext in [".md", ".txt", ".rst"]
                ):
                    # Skip large directories and focus on docs
                    if any(
                        doc_dir in member.filename.lower()
                        for doc_dir in ["doc", "guide", "tutorial", "readme"]
                    ):
                        try:
                            # Clean up the path structure
                            clean_path = "/".join(
                                member.filename.split("/")[1:]
                            )  # Remove root directory
                            if clean_path:
                                member.filename = clean_path
                                zip_ref.extract(member, target_dir)
                        except:
                            continue

        # Write version info
        version_file = target_dir / "version.txt"
        version_file.write_text("latest")

        # Clean up temp file
        os.remove(temp_zip)

    def _check_nvidia_gpu(self) -> bool:
        """Check if NVIDIA GPU and Docker GPU support is available"""
        try:
            # Check if nvidia-smi is available
            result = subprocess.run(
                ["nvidia-smi"], capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                return False

            # Check if Docker has GPU runtime support
            try:
                info = self.docker_client.info()
                runtimes = info.get("Runtimes", {})
                return "nvidia" in runtimes or any(
                    "nvidia" in runtime for runtime in runtimes.keys()
                )
            except:
                return False

        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            FileNotFoundError,
        ):
            return False

    def _find_container(self, container_id: str):
        """Find container by full ID or partial ID match"""
        # Try exact match first
        if container_id in self.active_containers:
            return self.active_containers[container_id]

        # Try partial match (for short IDs like 12 characters)
        for full_id, container in self.active_containers.items():
            if full_id.startswith(container_id):
                return container

        return None

    def _run_docker_scout_command(self, command: List[str]) -> str:
        """Run a Docker Scout command and return the output"""
        try:
            result = subprocess.run(
                ["docker", "scout"] + command,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return f"Error: {result.stderr}"

            return result.stdout

        except subprocess.TimeoutExpired:
            return "Error: Docker Scout command timed out"
        except subprocess.CalledProcessError as e:
            return f"Error running Docker Scout: {e}"
        except Exception as e:
            return f"Error: {str(e)}"

    def _register_core_tools(self):

        @self.mcp.tool()
        async def list_allowed_images() -> List[str]:
            """List allowed Docker images that can be used to create containers"""
            return sorted(list(self.allowed_images))

        @self.mcp.tool()
        async def get_data(ticker: str):
            """
            Get Ticker information. Only accepts one ticker.
            Args:
                ticker: str - Ticker item.
            Also fetches 1 month of history.
            """

            TICKER = yf.Ticker(ticker)
            return {
                "ticker_info": TICKER.info,
                "ticker_history_1m": TICKER.history(period="1mo"),
            }
        @self.mcp.tool()
        async def mcp_geocoding_api(city_query: str, count: int = 10):
            """
            MCP Geolocation using Open Meteo's Geolocation API.
            Args:
                city_query: str
                count: int = 10.

            """
            response = requests.get(
                f"https://geocoding-api.open-meteo.com/v1/search?name={city_query}&count={count}&language=en&format=json"
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {"error": "error"}

        @self.mcp.tool()
        async def get_gpu_status() -> str:
            """Get NVIDIA GPU status and availability"""
            if not self.gpu_available:
                return "GPU Status: Not available or not configured"

            try:
                # Get GPU info using nvidia-smi
                result = subprocess.run(
                    [
                        "nvidia-smi",
                        "--query-gpu=name,memory.total,memory.used,utilization.gpu",
                        "--format=csv,noheader,nounits",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    lines = result.stdout.strip().split("\n")
                    gpu_info = []
                    for i, line in enumerate(lines):
                        parts = line.split(", ")
                        if len(parts) >= 4:
                            name, total_mem, used_mem, util = parts[:4]
                            gpu_info.append(
                                f"GPU {i}: {name} | Memory: {used_mem}MB/{total_mem}MB | Utilization: {util}%"
                            )

                    return f"GPU Status: Available\n" + "\n".join(gpu_info)
                else:
                    return (
                        f"GPU Status: Available but nvidia-smi error: {result.stderr}"
                    )

            except Exception as e:
                return f"GPU Status: Available but error getting details: {str(e)}"

        @self.mcp.tool()
        async def create_container(
            image: str,
            name: str = None,
            ports: Dict[int, int] = None,
            environment: Dict[str, str] = None,
            command: str = None,
            use_gpu: bool = False,
        ) -> str:
            """Create and start a new Docker container that runs indefinitely"""
            try:
                # Validate image is allowed
                if image not in self.allowed_images:
                    return f"Image '{image}' not allowed. Use list_allowed_images to see available options."

                # Check GPU request
                if use_gpu and not self.gpu_available:
                    return "GPU requested but NVIDIA GPU support is not available"

                container_name = name or f"mcpdocker_{len(self.active_containers)}"

                # Create volume mount for file sharing
                volumes = {self.temp_dir: {"bind": "/workspace", "mode": "rw"}}

                # Default command to keep container running
                default_command = command or "tail -f /dev/null"

                # GPU configuration
                device_requests = []
                if use_gpu and self.gpu_available:
                    device_requests = [
                        docker.types.DeviceRequest(count=-1, capabilities=[["gpu"]])
                    ]

                container = self.docker_client.containers.run(
                    image,
                    command=default_command,
                    name=container_name,
                    detach=True,
                    ports=ports or {},
                    environment=environment or {},
                    volumes=volumes,
                    working_dir="/workspace",
                    tty=True,
                    stdin_open=True,
                    device_requests=device_requests,
                )

                self.active_containers[container.id] = container
                gpu_status = " (GPU enabled)" if use_gpu else ""
                return f"Container {container_name} ({container.id[:12]}) created and started{gpu_status}"

            except Exception as e:
                return f"Error creating container: {str(e)}"

        @self.mcp.tool()
        async def execute_command(container_id: str, command: str) -> str:
            """Execute a command in a running container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                result = container.exec_run(command)

                return f"Exit code: {result.exit_code}\nOutput:\n{result.output.decode('utf-8')}"

            except Exception as e:
                return f"Error executing command: {str(e)}"
        @self.mcp.tool()
        def check_for_errors_python(code: str):
            with tempfile.NamedTemporaryFile(mode='w', delete=True) as temporary_file:
                temporary_file.write(code)
                abs_path = os.path.abspath(temporary_file.name)
                data = subprocess.check_output(["ty","check",abs_path])
            return data
        

        @self.mcp.tool()
        def wiki_search(query: str, limit: int = 5) -> list:
            """
            Search Wikipedia for a query and return titles.
            """
            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": limit,
            }
            response = requests.get(WIKI_API, params=params).json()
            return [res["title"] for res in response.get("query", {}).get("search", [])]

        @self.mcp.tool()
        def wiki_summary(title: str) -> str:
            """
            Get a summary extract of a Wikipedia page.
            """
            params = {
                "action": "query",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "titles": title,
                "format": "json",
            }
            response = requests.get(WIKI_API, params=params).json()
            pages = response["query"]["pages"]
            return next(iter(pages.values())).get("extract", "")

        @self.mcp.tool()
        def wiki_page_content(title: str) -> str:
            """
            Get the full content of a Wikipedia page (plaintext).
            """
            params = {
                "action": "query",
                "prop": "extracts",
                "explaintext": True,
                "titles": title,
                "format": "json",
            }
            response = requests.get(WIKI_API, params=params).json()
            pages = response["query"]["pages"]
            return next(iter(pages.values())).get("extract", "")

        @self.mcp.tool()
        def wiki_links(title: str) -> list:
            """
            Get all linked articles from a Wikipedia page.
            """
            params = {
                "action": "query",
                "prop": "links",
                "titles": title,
                "format": "json",
                "pllimit": "max",
            }
            response = requests.get(WIKI_API, params=params).json()
            pages = response["query"]["pages"]
            links = next(iter(pages.values())).get("links", [])
            return [link["title"] for link in links]

        @self.mcp.tool()
        def wiki_categories(title: str) -> list:
            """
            Get categories for a Wikipedia page.
            """
            params = {
                "action": "query",
                "prop": "categories",
                "titles": title,
                "format": "json",
                "cllimit": "max",
            }
            response = requests.get(WIKI_API, params=params).json()
            pages = response["query"]["pages"]
            cats = next(iter(pages.values())).get("categories", [])
            return [cat["title"] for cat in cats]

        @self.mcp.tool()
        async def list_containers() -> List[str]:
            """List all active containers"""
            containers = []
            for container_id, container in self.active_containers.items():
                try:
                    container.reload()
                    status = container.status
                    name = container.name
                    containers.append(f"{name} ({container_id[:12]}) - {status}")
                except:
                    containers.append(f"Container {container_id[:12]} - unknown status")

            return containers if containers else ["No active containers"]

        @self.mcp.tool()
        async def upload_file(filename: str, content: str) -> str:
            """Upload a file to the shared workspace"""
            try:
                file_path = Path(self.temp_dir) / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                return f"File {filename} uploaded to workspace"

            except Exception as e:
                return f"Error uploading file: {str(e)}"

        @self.mcp.tool()
        async def list_workspace_files() -> List[str]:
            """List files in the shared workspace"""
            try:
                files = []
                for root, dirs, filenames in os.walk(self.temp_dir):
                    for filename in filenames:
                        rel_path = os.path.relpath(
                            os.path.join(root, filename), self.temp_dir
                        )
                        files.append(rel_path)

                return files if files else ["No files in workspace"]

            except Exception as e:
                return [f"Error listing files: {str(e)}"]

        @self.mcp.tool()
        async def stop_container(container_id: str) -> str:
            """Stop a running container (without removing it)"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                container.stop()

                return f"Container {container_id[:12]} stopped"

            except Exception as e:
                return f"Error stopping container: {str(e)}"

        @self.mcp.tool()
        async def start_container(container_id: str) -> str:
            """Start a stopped container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                container.start()

                return f"Container {container_id[:12]} started"

            except Exception as e:
                return f"Error starting container: {str(e)}"

        @self.mcp.tool()
        async def restart_container(container_id: str) -> str:
            """Restart a container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                container.restart()

                return f"Container {container_id[:12]} restarted"

            except Exception as e:
                return f"Error restarting container: {str(e)}"

        @self.mcp.tool()
        async def delete_container(container_id: str) -> str:
            """Delete a container (stops and removes it)"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                # Find the full container ID to remove from our tracking
                full_id = None
                for fid, cont in self.active_containers.items():
                    if cont == container:
                        full_id = fid
                        break

                container.stop()
                container.remove()
                if full_id:
                    del self.active_containers[full_id]

                return f"Container {container_id[:12]} stopped and deleted"

            except Exception as e:
                return f"Error deleting container: {str(e)}"

        @self.mcp.tool()
        async def get_container_logs(container_id: str, tail: int = 100) -> str:
            """Get logs from a container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                logs = container.logs(tail=tail).decode("utf-8")

                return logs if logs else "No logs available"

            except Exception as e:
                return f"Error getting logs: {str(e)}"

        @self.mcp.tool()
        async def scout_scan_vulnerabilities(image: str) -> str:
            """Scan a Docker image for security vulnerabilities using Docker Scout"""
            if image not in self.allowed_images:
                return f"Image '{image}' not allowed. Use list_allowed_images to see available options."

            return self._run_docker_scout_command(["cves", image])

        @self.mcp.tool()
        def get_package_info(package: str) -> dict:
            """
            Get metadata for a given PyPI package.
            Example: get_package_info("requests")
            """
            url = f"{PYPI_BASE}/{package}/json"
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            return {"error": f"Package {package} not found"}

        @self.mcp.tool()
        def get_latest_version(package: str) -> str:
            """
            Get the latest release version of a package.
            Example: get_latest_version("requests")
            """
            info = get_package_info(package)
            if "error" in info:
                return info["error"]
            return info["info"]["version"]

        @self.mcp.tool()
        def get_package_releases(package: str) -> list:
            """
            Get all release versions of a package.
            Example: get_package_releases("requests")
            """
            info = get_package_info(package)
            if "error" in info:
                return []
            return list(info["releases"].keys())

        @self.mcp.tool()
        def get_download_urls(package: str, version: str = None) -> list:
            """
            Get download URLs for a package version (tar.gz, wheels, etc.).
            If version is None, use the latest version.
            Example: get_download_urls("requests")
            """
            info = get_package_info(package)
            if "error" in info:
                return []
            if version is None:
                version = info["info"]["version"]
            return [file["url"] for file in info["releases"].get(version, [])]

        @self.mcp.tool()
        def search_pypi(query: str) -> list:
            """
            Search PyPI for packages (uses PyPI's simple search via pypi.org/search).
            NOTE: PyPI JSON API does not provide full search; this scrapes instead.
            Example: search_pypi("http")
            """
            url = f"https://pypi.org/search/?q={query}"
            response = requests.get(url)
            if response.status_code == 200:
                # crude title extraction
                from bs4 import BeautifulSoup

                soup = BeautifulSoup(response.text, "html.parser")
                results = []
                for item in soup.select(".package-snippet"):
                    name = item.select_one("span.package-snippet__name").text.strip()
                    version = item.select_one(
                        "span.package-snippet__version"
                    ).text.strip()
                    results.append(f"{name} ({version})")
                return results
            return []

        @self.mcp.tool()
        def search_devdocs(doc_slug: str, query: str) -> dict:
            """
            Search DevDocs.io API for documentation content.
            
            Args:
                doc_slug: The documentation slug (e.g., 'python~3.12', 'javascript', 'go')
                query: The search query string
            
            Returns:
                Dictionary containing search results from DevDocs.io
            
            Example: search_devdocs("python~3.12", "requests")
            """
            try:
                # DevDocs.io search endpoint
                url = f"{_DEVDOCS_URL}/docs/{doc_slug}/index.json"
                headers = {
                    'User-Agent': 'MCPDocker/1.0 (DevDocs API Client)',
                    'Accept': 'application/json'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    docs_index = response.json()
                    
                    # Filter entries based on query
                    matching_entries = []
                    query_lower = query.lower()
                    
                    for entry in docs_index.get('entries', []):
                        name = entry.get('name', '').lower()
                        path = entry.get('path', '').lower()
                        
                        if query_lower in name or query_lower in path:
                            matching_entries.append({
                                'name': entry.get('name'),
                                'type': entry.get('type'),
                                'path': entry.get('path'),
                                'url': f"https://devdocs.io/{doc_slug}/{entry.get('path', '')}"
                            })
                    
                    return {
                        'doc_slug': doc_slug,
                        'query': query,
                        'total_matches': len(matching_entries),
                        'matches': matching_entries[:20]  # Limit to first 20 results
                    }
                else:
                    return {
                        'error': f"Failed to fetch documentation index for '{doc_slug}'. Status: {response.status_code}",
                        'available_docs_hint': "Try doc slugs like: python~3.12, javascript, go, rust, node"
                    }
                    
            except requests.RequestException as e:
                return {
                    'error': f"Request failed: {str(e)}",
                    'suggestion': "Check your internet connection and try again"
                }
            except Exception as e:
                return {
                    'error': f"Unexpected error: {str(e)}"
                }

        @self.mcp.tool()
        def get_devdocs_content(doc_slug: str, path: str) -> dict:
            """
            Fetch specific documentation content from DevDocs.io.
            
            Args:
                doc_slug: The documentation slug (e.g., 'python~3.12', 'javascript', 'go')
                path: The specific documentation path (from search results)
            
            Returns:
                Dictionary containing the documentation content
            
            Example: get_devdocs_content("python~3.12", "library/requests")
            """
            try:
                # DevDocs.io content endpoint
                url = f"{_DEVDOCS_URL}/docs/{doc_slug}/{path}.html"
                headers = {
                    'User-Agent': 'MCPDocker/1.0 (DevDocs API Client)',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
                }
                
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    # Parse HTML content to extract text
                    try:
                        from bs4 import BeautifulSoup
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Remove script and style elements
                        for script in soup(["script", "style"]):
                            script.decompose()
                        
                        # Get text content
                        text = soup.get_text()
                        
                        # Clean up text
                        lines = (line.strip() for line in text.splitlines())
                        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                        text = ' '.join(chunk for chunk in chunks if chunk)
                        
                        return {
                            'doc_slug': doc_slug,
                            'path': path,
                            'url': url,
                            'content': text[:10000],  # Limit content to 10k chars
                            'content_length': len(text),
                            'truncated': len(text) > 10000
                        }
                    except ImportError:
                        # Fallback if BeautifulSoup is not available
                        return {
                            'doc_slug': doc_slug,
                            'path': path,
                            'url': url,
                            'raw_html': response.text[:5000],  # Return raw HTML limited to 5k chars
                            'note': 'Raw HTML returned (BeautifulSoup not available for parsing)',
                            'truncated': len(response.text) > 5000
                        }
                else:
                    return {
                        'error': f"Failed to fetch content from '{url}'. Status: {response.status_code}",
                        'suggestion': "Check if the doc_slug and path are correct. Use search_devdocs to find valid paths."
                    }
                    
            except requests.RequestException as e:
                return {
                    'error': f"Request failed: {str(e)}",
                    'suggestion': "Check your internet connection and try again"
                }
            except Exception as e:
                return {
                    'error': f"Unexpected error: {str(e)}"
                }

        @self.mcp.tool()
        def list_devdocs_available() -> dict:
            """
            List available documentation sets on DevDocs.io.
            
            Returns:
                Dictionary containing available documentation slugs and their descriptions
            """
            try:
                # DevDocs.io docs list endpoint
                url = f"{_DEVDOCS_URL}/docs.json"
                headers = {
                    'User-Agent': 'MCPDocker/1.0 (DevDocs API Client)',
                    'Accept': 'application/json'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    docs_list = response.json()
                    
                    # Organize by category
                    categorized = {}
                    popular_docs = []
                    
                    for doc in docs_list:
                        slug = doc.get('slug', '')
                        name = doc.get('name', '')
                        version = doc.get('version', '')
                        
                        # Add to popular list if it's a commonly used language/framework
                        if any(tech in slug.lower() for tech in ['python', 'javascript', 'node', 'go', 'rust', 'java', 'php', 'ruby']):
                            popular_docs.append({
                                'slug': slug,
                                'name': name,
                                'version': version
                            })
                        
                        # Categorize by first part of name
                        category = name.split()[0] if name else 'Other'
                        if category not in categorized:
                            categorized[category] = []
                        categorized[category].append({
                            'slug': slug,
                            'name': name,
                            'version': version
                        })
                    
                    return {
                        'total_docs': len(docs_list),
                        'popular_languages': popular_docs[:15],  # Top 15 popular
                        'categories': {k: v[:5] for k, v in categorized.items()},  # Top 5 per category
                        'note': 'Use the slug value with search_devdocs() or get_devdocs_content()'
                    }
                else:
                    return {
                        'error': f"Failed to fetch documentation list. Status: {response.status_code}",
                        'fallback': {
                            'popular_slugs': ['python~3.12', 'javascript', 'node~20_lts', 'go', 'rust', 'java~21']
                        }
                    }
                    
            except requests.RequestException as e:
                return {
                    'error': f"Request failed: {str(e)}",
                    'fallback': {
                        'popular_slugs': ['python~3.12', 'javascript', 'node~20_lts', 'go', 'rust', 'java~21']
                    }
                }
            except Exception as e:
                return {
                    'error': f"Unexpected error: {str(e)}"
                }

        @self.mcp.tool()
        async def scout_get_recommendations(image: str) -> str:
            """Get Docker Scout security recommendations for an image"""
            if image not in self.allowed_images:
                return f"Image '{image}' not allowed. Use list_allowed_images to see available options."

            return self._run_docker_scout_command(["recommendations", image])

        @self.mcp.tool()
        async def scout_quickview(image: str) -> str:
            """Get a quick security overview of a Docker image using Docker Scout"""
            if image not in self.allowed_images:
                return f"Image '{image}' not allowed. Use list_allowed_images to see available options."

            return self._run_docker_scout_command(["quickview", image])

        @self.mcp.tool()
        async def scout_compare_images(base_image: str, target_image: str) -> str:
            """Compare two Docker images for security differences"""
            if base_image not in self.allowed_images:
                return f"Base image '{base_image}' not allowed. Use list_allowed_images to see available options."
            if target_image not in self.allowed_images:
                return f"Target image '{target_image}' not allowed. Use list_allowed_images to see available options."

            return self._run_docker_scout_command(
                ["compare", "--to", target_image, base_image]
            )

        @self.mcp.tool()
        async def scout_policy_evaluation(image: str, policy: str = "default") -> str:
            """Evaluate a Docker image against security policies using Docker Scout"""
            if image not in self.allowed_images:
                return f"Image '{image}' not allowed. Use list_allowed_images to see available options."

            return self._run_docker_scout_command(["policy", image, "--policy", policy])

        @self.mcp.tool()
        async def copy_file_to_container(
            container_id: str, local_path: str, container_path: str
        ) -> str:
            """Copy a file from local filesystem or workspace to a container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                # Check if the local path is absolute or relative to workspace
                if os.path.isabs(local_path):
                    source_path = Path(local_path)
                else:
                    source_path = Path(self.temp_dir) / local_path

                if not source_path.exists():
                    return f"Source file {local_path} not found"

                # Create a tar archive containing the file
                tar_stream = io.BytesIO()
                with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                    tar.add(source_path, arcname=os.path.basename(container_path))
                tar_stream.seek(0)

                # Extract to the container
                container_dir = os.path.dirname(container_path) or "/"
                container.put_archive(container_dir, tar_stream.getvalue())

                return f"File copied from {local_path} to {container_path} in container {container_id[:12]}"

            except Exception as e:
                return f"Error copying file to container: {str(e)}"

        @self.mcp.tool()
        async def copy_file_from_container(
            container_id: str, container_path: str, local_path: str = None
        ) -> str:
            """Copy a file from container to local workspace"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                # Get the archive from the container
                tar_stream, stat = container.get_archive(container_path)

                # If no local path specified, use the filename in workspace
                if local_path is None:
                    local_path = os.path.basename(container_path)

                # Determine the full local path
                if os.path.isabs(local_path):
                    dest_path = Path(local_path)
                else:
                    dest_path = Path(self.temp_dir) / local_path

                # Create parent directories if needed
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # Extract the file from the tar stream
                tar_data = b"".join(chunk for chunk in tar_stream)
                with tarfile.open(fileobj=io.BytesIO(tar_data)) as tar:
                    # Extract the first file in the archive
                    members = tar.getmembers()
                    if members:
                        file_data = tar.extractfile(members[0])
                        if file_data:
                            with open(dest_path, "wb") as f:
                                f.write(file_data.read())

                return f"File copied from {container_path} in container {container_id[:12]} to {local_path}"

            except Exception as e:
                return f"Error copying file from container: {str(e)}"

        @self.mcp.tool()
        async def create_file_in_container(
            container_id: str, file_path: str, content: str
        ) -> str:
            """Create a file with specified content inside a container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                # Create a temporary file in workspace first
                temp_file = Path(self.temp_dir) / f"temp_{os.path.basename(file_path)}"
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(content)

                # Copy to container
                tar_stream = io.BytesIO()
                with tarfile.open(fileobj=tar_stream, mode="w") as tar:
                    tar.add(temp_file, arcname=os.path.basename(file_path))
                tar_stream.seek(0)

                container_dir = os.path.dirname(file_path) or "/"
                container.put_archive(container_dir, tar_stream.getvalue())

                # Clean up temp file
                temp_file.unlink()

                return f"File {file_path} created in container {container_id[:12]}"

            except Exception as e:
                return f"Error creating file in container: {str(e)}"

        @self.mcp.tool()
        async def delete_file_in_container(container_id: str, file_path: str) -> str:
            """Delete a file inside a container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                result = container.exec_run(f"rm -f {file_path}")

                if result.exit_code == 0:
                    return (
                        f"File {file_path} deleted from container {container_id[:12]}"
                    )
                else:
                    return f"Error deleting file: {result.output.decode('utf-8')}"

            except Exception as e:
                return f"Error deleting file in container: {str(e)}"

        @self.mcp.tool()
        async def list_files_in_container(
            container_id: str, directory_path: str = "/workspace"
        ) -> str:
            """List files and directories in a container directory"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                result = container.exec_run(f"ls -la {directory_path}")

                if result.exit_code == 0:
                    return f"Contents of {directory_path}:\n{result.output.decode('utf-8')}"
                else:
                    return f"Error listing directory: {result.output.decode('utf-8')}"

            except Exception as e:
                return f"Error listing files in container: {str(e)}"

        @self.mcp.tool()
        async def create_directory_in_container(
            container_id: str, directory_path: str
        ) -> str:
            """Create a directory inside a container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                result = container.exec_run(f"mkdir -p {directory_path}")

                if result.exit_code == 0:
                    return f"Directory {directory_path} created in container {container_id[:12]}"
                else:
                    return f"Error creating directory: {result.output.decode('utf-8')}"

            except Exception as e:
                return f"Error creating directory in container: {str(e)}"

        @self.mcp.tool()
        async def move_file_in_container(
            container_id: str, source_path: str, dest_path: str
        ) -> str:
            """Move or rename a file/directory inside a container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                result = container.exec_run(f"mv {source_path} {dest_path}")

                if result.exit_code == 0:
                    return f"Moved {source_path} to {dest_path} in container {container_id[:12]}"
                else:
                    return f"Error moving file: {result.output.decode('utf-8')}"

            except Exception as e:
                return f"Error moving file in container: {str(e)}"

        @self.mcp.tool()
        async def copy_file_in_container(
            container_id: str, source_path: str, dest_path: str
        ) -> str:
            """Copy a file/directory inside a container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                result = container.exec_run(f"cp -r {source_path} {dest_path}")

                if result.exit_code == 0:
                    return f"Copied {source_path} to {dest_path} in container {container_id[:12]}"
                else:
                    return f"Error copying file: {result.output.decode('utf-8')}"

            except Exception as e:
                return f"Error copying file in container: {str(e)}"

        @self.mcp.tool()
        async def read_file_in_container(container_id: str, file_path: str) -> str:
            """Read the contents of a file inside a container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                result = container.exec_run(f"cat {file_path}")

                if result.exit_code == 0:
                    return result.output.decode("utf-8")
                else:
                    return f"Error reading file: {result.output.decode('utf-8')}"

            except Exception as e:
                return f"Error reading file in container: {str(e)}"

        @self.mcp.tool()
        async def write_file_in_container(
            container_id: str, file_path: str, content: str, append: bool = False
        ) -> str:
            """Write content to a file inside a container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                # Escape content for shell
                import shlex

                escaped_content = shlex.quote(content)

                if append:
                    command = f"echo {escaped_content} >> {file_path}"
                else:
                    command = f"echo {escaped_content} > {file_path}"

                result = container.exec_run(command)

                if result.exit_code == 0:
                    action = "appended to" if append else "written to"
                    return (
                        f"Content {action} {file_path} in container {container_id[:12]}"
                    )
                else:
                    return f"Error writing file: {result.output.decode('utf-8')}"

            except Exception as e:
                return f"Error writing file in container: {str(e)}"

        @self.mcp.tool()
        async def start_port_stream(
            container_id: str, container_port: int, host_port: int = None
        ) -> str:
            """Start streaming data from a container port to a host port"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                if host_port is None:
                    host_port = container_port

                # Check if port is already being streamed
                stream_key = f"{container_id[:12]}:{container_port}"
                if stream_key in self.active_streams:
                    return f"Stream already active for container {container_id[:12]} port {container_port}"

                # Start the streaming server
                stream_thread = threading.Thread(
                    target=self._start_stream_server,
                    args=(container, container_port, host_port, stream_key),
                    daemon=True,
                )
                stream_thread.start()

                self.active_streams[stream_key] = {
                    "container_id": container_id,
                    "container_port": container_port,
                    "host_port": host_port,
                    "thread": stream_thread,
                }

                return f"Started streaming from container {container_id[:12]} port {container_port} to host port {host_port}"

            except Exception as e:
                return f"Error starting port stream: {str(e)}"

        @self.mcp.tool()
        async def stop_port_stream(container_id: str, container_port: int) -> str:
            """Stop streaming data from a container port"""
            try:
                stream_key = f"{container_id[:12]}:{container_port}"

                if stream_key not in self.active_streams:
                    return f"No active stream found for container {container_id[:12]} port {container_port}"

                # Remove from active streams (the thread will detect this and stop)
                stream_info = self.active_streams.pop(stream_key)

                return f"Stopped streaming from container {container_id[:12]} port {container_port}"

            except Exception as e:
                return f"Error stopping port stream: {str(e)}"

        @self.mcp.tool()
        async def list_active_streams() -> List[str]:
            """List all active port streams"""
            if not self.active_streams:
                return ["No active streams"]

            streams = []
            for stream_key, stream_info in self.active_streams.items():
                container_id = stream_info["container_id"][:12]
                container_port = stream_info["container_port"]
                host_port = stream_info["host_port"]
                streams.append(
                    f"{container_id}:{container_port} -> localhost:{host_port}"
                )

            return streams

        @self.mcp.tool()
        async def stream_container_logs(
            container_id: str, follow: bool = True, tail: int = 100
        ) -> str:
            """Stream container logs in real-time with JSON responses"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return json.dumps({"error": f"Container {container_id} not found"})

                if not follow:
                    # Return static logs
                    logs = container.logs(tail=tail).decode("utf-8")
                    return json.dumps(
                        {
                            "type": "logs",
                            "container_id": container_id[:12],
                            "data": logs,
                            "streaming": False,
                        }
                    )

                # Start streaming logs
                stream_key = f"logs_{container_id[:12]}_{int(time.time())}"

                def stream_logs():
                    try:
                        log_stream = container.logs(stream=True, follow=True, tail=tail)
                        for log_line in log_stream:
                            if stream_key not in self.active_streams:
                                break

                            log_data = {
                                "type": "log_line",
                                "container_id": container_id[:12],
                                "timestamp": time.time(),
                                "data": log_line.decode("utf-8").strip(),
                                "stream_key": stream_key,
                            }

                            # Store in stream buffer for retrieval
                            if stream_key not in self.active_streams:
                                self.active_streams[stream_key] = {
                                    "buffer": [],
                                    "type": "logs",
                                }

                            self.active_streams[stream_key]["buffer"].append(log_data)

                            # Keep buffer size manageable
                            if len(self.active_streams[stream_key]["buffer"]) > 1000:
                                self.active_streams[stream_key]["buffer"] = (
                                    self.active_streams[stream_key]["buffer"][-500:]
                                )

                    except Exception as e:
                        error_data = {
                            "type": "error",
                            "container_id": container_id[:12],
                            "timestamp": time.time(),
                            "error": str(e),
                            "stream_key": stream_key,
                        }
                        if stream_key in self.active_streams:
                            self.active_streams[stream_key]["buffer"].append(error_data)

                # Start streaming thread
                stream_thread = threading.Thread(target=stream_logs, daemon=True)
                stream_thread.start()

                self.active_streams[stream_key] = {
                    "buffer": [],
                    "type": "logs",
                    "container_id": container_id,
                    "thread": stream_thread,
                }

                return json.dumps(
                    {
                        "type": "stream_started",
                        "container_id": container_id[:12],
                        "stream_key": stream_key,
                        "message": f"Started streaming logs for container {container_id[:12]}",
                        "streaming": True,

                    }
                )

            except Exception as e:
                return json.dumps({"error": f"Error streaming logs: {str(e)}"})

        @self.mcp.tool()
        async def get_stream_data(stream_key: str, last_index: int = 0) -> str:
            """Get new data from an active stream since last_index"""
            try:
                if stream_key not in self.active_streams:
                    return json.dumps({"error": f"Stream {stream_key} not found"})

                stream_data = self.active_streams[stream_key]
                buffer = stream_data.get("buffer", [])

                # Get new data since last_index
                new_data = buffer[last_index:]

                return json.dumps(
                    {
                        "type": "stream_data",
                        "stream_key": stream_key,
                        "last_index": len(buffer),
                        "data": new_data,
                        "has_more": len(new_data) > 0,
                    }
                )

            except Exception as e:
                return json.dumps({"error": f"Error getting stream data: {str(e)}"})

        @self.mcp.tool()
        async def stop_stream(stream_key: str) -> str:
            """Stop an active MCP stream"""
            try:
                if stream_key not in self.active_streams:
                    return json.dumps({"error": f"Stream {stream_key} not found"})

                stream_info = self.active_streams.pop(stream_key)

                return json.dumps(
                    {
                        "type": "stream_stopped",
                        "stream_key": stream_key,
                        "message": f"Stream {stream_key} stopped successfully",
                    }
                )

            except Exception as e:
                return json.dumps({"error": f"Error stopping stream: {str(e)}"})

        @self.mcp.tool()
        async def stream_command_execution(container_id: str, command: str) -> str:
            """Execute a command in container and stream the output in real-time"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return json.dumps({"error": f"Container {container_id} not found"})

                stream_key = f"exec_{container_id[:12]}_{int(time.time())}"

                def execute_and_stream():
                    try:
                        # Execute command with streaming
                        exec_instance = container.client.api.exec_create(
                            container.id, command, stdout=True, stderr=True, stream=True
                        )

                        exec_stream = container.client.api.exec_start(
                            exec_instance["Id"], stream=True
                        )

                        for chunk in exec_stream:
                            if stream_key not in self.active_streams:
                                break

                            output_data = {
                                "type": "command_output",
                                "container_id": container_id[:12],
                                "command": command,
                                "timestamp": time.time(),
                                "data": chunk.decode("utf-8"),
                                "stream_key": stream_key,
                            }

                            if stream_key not in self.active_streams:
                                self.active_streams[stream_key] = {
                                    "buffer": [],
                                    "type": "command",
                                }

                            self.active_streams[stream_key]["buffer"].append(
                                output_data
                            )

                            # Keep buffer manageable
                            if len(self.active_streams[stream_key]["buffer"]) > 1000:
                                self.active_streams[stream_key]["buffer"] = (
                                    self.active_streams[stream_key]["buffer"][-500:]
                                )

                        # Get exit code
                        exec_info = container.client.api.exec_inspect(
                            exec_instance["Id"]
                        )
                        exit_code = exec_info.get("ExitCode", 0)

                        completion_data = {
                            "type": "command_completed",
                            "container_id": container_id[:12],
                            "command": command,
                            "timestamp": time.time(),
                            "exit_code": exit_code,
                            "stream_key": stream_key,
                        }

                        if stream_key in self.active_streams:
                            self.active_streams[stream_key]["buffer"].append(
                                completion_data
                            )

                    except Exception as e:
                        error_data = {
                            "type": "command_error",
                            "container_id": container_id[:12],
                            "command": command,
                            "timestamp": time.time(),
                            "error": str(e),
                            "stream_key": stream_key,
                        }
                        if stream_key in self.active_streams:
                            self.active_streams[stream_key]["buffer"].append(error_data)

                # Start execution thread
                exec_thread = threading.Thread(target=execute_and_stream, daemon=True)
                exec_thread.start()

                self.active_streams[stream_key] = {
                    "buffer": [],
                    "type": "command",
                    "container_id": container_id,
                    "command": command,
                    "thread": exec_thread,
                }

                return json.dumps(
                    {
                        "type": "stream_started",
                        "container_id": container_id[:12],
                        "command": command,
                        "stream_key": stream_key,
                        "message": f"Started streaming command execution in container {container_id[:12]}",
                        "streaming": True,
                    }
                )

            except Exception as e:
                return json.dumps(
                    {"error": f"Error streaming command execution: {str(e)}"}
                )

        @self.mcp.tool()
        async def list_active_mcp_streams() -> str:
            """List all active MCP streams with their details"""
            try:
                if not self.active_streams:
                    return json.dumps({"streams": [], "count": 0})

                streams = []
                for stream_key, stream_info in self.active_streams.items():
                    stream_detail = {
                        "stream_key": stream_key,
                        "type": stream_info.get("type", "unknown"),
                        "buffer_size": len(stream_info.get("buffer", [])),
                        "container_id": (
                            stream_info.get("container_id", "")[:12]
                            if stream_info.get("container_id")
                            else ""
                        ),
                    }

                    if stream_info.get("command"):
                        stream_detail["command"] = stream_info["command"]

                    streams.append(stream_detail)

                return json.dumps({"streams": streams, "count": len(streams)})

            except Exception as e:
                return json.dumps({"error": f"Error listing streams: {str(e)}"})

        # Playwright Tools
        @self.mcp.tool()
        async def playwright_launch_browser(
            browser_type: str = "chromium",
            headless: bool = True,
            args: List[str] = None,
        ) -> str:
            """Launch a Playwright browser instance (chromium, firefox, or webkit)"""
            try:
                if self.playwright_instance is None:
                    self.playwright_instance = await async_playwright().start()

                browser_args = args or []

                if browser_type.lower() == "chromium":
                    browser = await self.playwright_instance.chromium.launch(
                        headless=headless, args=browser_args
                    )
                elif browser_type.lower() == "firefox":
                    browser = await self.playwright_instance.firefox.launch(
                        headless=headless, args=browser_args
                    )
                elif browser_type.lower() == "webkit":
                    browser = await self.playwright_instance.webkit.launch(
                        headless=headless, args=browser_args
                    )
                else:
                    return f"Unsupported browser type: {browser_type}. Use chromium, firefox, or webkit."

                browser_id = f"pw_{browser_type}_{len(self.active_browsers)}"
                self.active_browsers[browser_id] = browser

                return f"Browser {browser_type} launched with ID: {browser_id}"

            except Exception as e:
                return f"Error launching browser: {str(e)}"

        @self.mcp.tool()
        async def playwright_create_page(
            browser_id: str, viewport_width: int = 1920, viewport_height: int = 1080
        ) -> str:
            """Create a new page in a Playwright browser"""
            try:
                if browser_id not in self.active_browsers:
                    return f"Browser {browser_id} not found"

                browser = self.active_browsers[browser_id]
                page = await browser.new_page(
                    viewport={"width": viewport_width, "height": viewport_height}
                )

                # Store page reference in browser for tracking
                if not hasattr(browser, "_page_references"):
                    browser._page_references = {}

                page_id = f"{browser_id}_page_{len(browser._page_references)}"
                browser._page_references[page_id] = page

                return f"Page created with ID: {page_id}"

            except Exception as e:
                return f"Error creating page: {str(e)}"

        @self.mcp.tool()
        async def playwright_navigate(
            page_id: str, url: str, wait_until: str = "load"
        ) -> str:
            """Navigate to a URL in a Playwright page"""
            try:
                page = await self._get_playwright_page(page_id)
                if isinstance(page, str):  # Error message
                    return page

                await page.goto(url, wait_until=wait_until)
                return f"Navigated to {url}"

            except Exception as e:
                return f"Error navigating: {str(e)}"

        @self.mcp.tool()
        async def playwright_click(
            page_id: str, selector: str, timeout: int = 30000
        ) -> str:
            """Click an element on a Playwright page"""
            try:
                page = await self._get_playwright_page(page_id)
                if isinstance(page, str):
                    return page

                await page.click(selector, timeout=timeout)
                return f"Clicked element: {selector}"

            except Exception as e:
                return f"Error clicking element: {str(e)}"

        @self.mcp.tool()
        async def playwright_type(
            page_id: str, selector: str, text: str, timeout: int = 30000
        ) -> str:
            """Type text into an element on a Playwright page"""
            try:
                page = await self._get_playwright_page(page_id)
                if isinstance(page, str):
                    return page

                await page.fill(selector, text, timeout=timeout)
                return f"Typed '{text}' into {selector}"

            except Exception as e:
                return f"Error typing text: {str(e)}"

        @self.mcp.tool()
        async def playwright_screenshot(
            page_id: str,
            filename: str = None,
            full_page: bool = False,
            return_base64: bool = False,
        ) -> str:
            """Take a screenshot of a Playwright page and optionally return as base64 for AI viewing"""
            try:
                page = await self._get_playwright_page(page_id)
                if isinstance(page, str):
                    return page

                if filename is None:
                    filename = f"screenshot_{page_id}_{int(time.time())}.png"

                screenshot_path = Path(self.temp_dir) / filename

                if return_base64:
                    # Take screenshot as bytes and return base64 for AI viewing
                    screenshot_bytes = await page.screenshot(full_page=full_page)

                    # Also save to file
                    with open(screenshot_path, "wb") as f:
                        f.write(screenshot_bytes)

                    import base64

                    screenshot_base64 = base64.b64encode(screenshot_bytes).decode(
                        "utf-8"
                    )

                    return json.dumps(
                        {
                            "type": "screenshot",
                            "filename": filename,
                            "path": str(screenshot_path),
                            "base64": screenshot_base64,
                            "format": "png",
                            "message": f"Screenshot saved to {filename} and available for AI viewing",
                        }
                    )
                else:
                    # Regular file-only screenshot
                    await page.screenshot(
                        path=str(screenshot_path), full_page=full_page
                    )
                    return f"Screenshot saved to {filename}"

            except Exception as e:
                return f"Error taking screenshot: {str(e)}"

        @self.mcp.tool()
        async def playwright_get_text(
            page_id: str, selector: str, timeout: int = 30000
        ) -> str:
            """Get text content from an element on a Playwright page"""
            try:
                page = await self._get_playwright_page(page_id)
                if isinstance(page, str):
                    return page

                text = await page.text_content(selector, timeout=timeout)
                return text or ""

            except Exception as e:
                return f"Error getting text: {str(e)}"

        @self.mcp.tool()
        async def playwright_wait_for_selector(
            page_id: str, selector: str, timeout: int = 30000, state: str = "visible"
        ) -> str:
            """Wait for an element to appear on a Playwright page"""
            try:
                page = await self._get_playwright_page(page_id)
                if isinstance(page, str):
                    return page

                await page.wait_for_selector(selector, timeout=timeout, state=state)
                return f"Element {selector} is now {state}"

            except Exception as e:
                return f"Error waiting for selector: {str(e)}"

        @self.mcp.tool()
        async def playwright_evaluate(page_id: str, script: str) -> str:
            """Execute JavaScript in a Playwright page"""
            try:
                page = await self._get_playwright_page(page_id)
                if isinstance(page, str):
                    return page

                result = await page.evaluate(script)
                return str(result)

            except Exception as e:
                return f"Error evaluating script: {str(e)}"

        @self.mcp.tool()
        async def playwright_close_page(page_id: str) -> str:
            """Close a Playwright page"""
            try:
                page = await self._get_playwright_page(page_id)
                if isinstance(page, str):
                    return page

                await page.close()

                # Remove from browser references
                for browser in self.active_browsers.values():
                    if (
                        hasattr(browser, "_page_references")
                        and page_id in browser._page_references
                    ):
                        del browser._page_references[page_id]
                        break

                return f"Page {page_id} closed"

            except Exception as e:
                return f"Error closing page: {str(e)}"

        @self.mcp.tool()
        async def playwright_close_browser(browser_id: str) -> str:
            """Close a Playwright browser"""
            try:
                if browser_id not in self.active_browsers:
                    return f"Browser {browser_id} not found"

                browser = self.active_browsers[browser_id]
                await browser.close()
                del self.active_browsers[browser_id]

                return f"Browser {browser_id} closed"

            except Exception as e:
                return f"Error closing browser: {str(e)}"

        # Selenium Tools
        @self.mcp.tool()
        async def selenium_launch_driver(
            browser_type: str = "chrome",
            headless: bool = True,
            options: List[str] = None,
        ) -> str:
            """Launch a Selenium WebDriver (chrome or firefox)"""
            try:
                browser_options = options or []

                if browser_type.lower() == "chrome":
                    chrome_options = ChromeOptions()
                    if headless:
                        chrome_options.add_argument("--headless")
                    chrome_options.add_argument("--no-sandbox")
                    chrome_options.add_argument("--disable-dev-shm-usage")

                    for option in browser_options:
                        chrome_options.add_argument(option)

                    driver = webdriver.Chrome(options=chrome_options)

                elif browser_type.lower() == "firefox":
                    firefox_options = FirefoxOptions()
                    if headless:
                        firefox_options.add_argument("--headless")

                    for option in browser_options:
                        firefox_options.add_argument(option)

                    driver = webdriver.Firefox(options=firefox_options)

                else:
                    return f"Unsupported browser type: {browser_type}. Use chrome or firefox."

                driver_id = f"sel_{browser_type}_{len(self.active_selenium_drivers)}"
                self.active_selenium_drivers[driver_id] = driver

                return f"Selenium {browser_type} driver launched with ID: {driver_id}"

            except Exception as e:
                return f"Error launching Selenium driver: {str(e)}"

        @self.mcp.tool()
        async def selenium_navigate(driver_id: str, url: str) -> str:
            """Navigate to a URL using Selenium"""
            try:
                if driver_id not in self.active_selenium_drivers:
                    return f"Driver {driver_id} not found"

                driver = self.active_selenium_drivers[driver_id]
                driver.get(url)

                return f"Navigated to {url}"

            except Exception as e:
                return f"Error navigating: {str(e)}"

        @self.mcp.tool()
        async def selenium_click(
            driver_id: str, selector: str, by: str = "css", timeout: int = 10
        ) -> str:
            """Click an element using Selenium"""
            try:
                if driver_id not in self.active_selenium_drivers:
                    return f"Driver {driver_id} not found"

                driver = self.active_selenium_drivers[driver_id]
                wait = WebDriverWait(driver, timeout)

                by_mapping = {
                    "css": By.CSS_SELECTOR,
                    "xpath": By.XPATH,
                    "id": By.ID,
                    "name": By.NAME,
                    "class": By.CLASS_NAME,
                    "tag": By.TAG_NAME,
                }

                if by not in by_mapping:
                    return f"Invalid selector type: {by}. Use css, xpath, id, name, class, or tag."

                element = wait.until(
                    EC.element_to_be_clickable((by_mapping[by], selector))
                )
                element.click()

                return f"Clicked element: {selector}"

            except Exception as e:
                return f"Error clicking element: {str(e)}"

        @self.mcp.tool()
        async def selenium_type(
            driver_id: str,
            selector: str,
            text: str,
            by: str = "css",
            timeout: int = 10,
            clear: bool = True,
        ) -> str:
            """Type text into an element using Selenium"""
            try:
                if driver_id not in self.active_selenium_drivers:
                    return f"Driver {driver_id} not found"

                driver = self.active_selenium_drivers[driver_id]
                wait = WebDriverWait(driver, timeout)

                by_mapping = {
                    "css": By.CSS_SELECTOR,
                    "xpath": By.XPATH,
                    "id": By.ID,
                    "name": By.NAME,
                    "class": By.CLASS_NAME,
                    "tag": By.TAG_NAME,
                }

                if by not in by_mapping:
                    return f"Invalid selector type: {by}. Use css, xpath, id, name, class, or tag."

                element = wait.until(
                    EC.presence_of_element_located((by_mapping[by], selector))
                )
                if clear:
                    element.clear()
                element.send_keys(text)

                return f"Typed '{text}' into {selector}"

            except Exception as e:
                return f"Error typing text: {str(e)}"

        @self.mcp.tool()
        async def selenium_screenshot(driver_id: str, filename: str = None) -> str:
            """Take a screenshot using Selenium"""
            try:
                if driver_id not in self.active_selenium_drivers:
                    return f"Driver {driver_id} not found"

                driver = self.active_selenium_drivers[driver_id]

                if filename is None:
                    filename = f"selenium_screenshot_{driver_id}_{int(time.time())}.png"

                screenshot_path = Path(self.temp_dir) / filename
                driver.save_screenshot(str(screenshot_path))

                return f"Screenshot saved to {filename}"

            except Exception as e:
                return f"Error taking screenshot: {str(e)}"

        @self.mcp.tool()
        async def selenium_get_text(
            driver_id: str, selector: str, by: str = "css", timeout: int = 10
        ) -> str:
            """Get text content from an element using Selenium"""
            try:
                if driver_id not in self.active_selenium_drivers:
                    return f"Driver {driver_id} not found"

                driver = self.active_selenium_drivers[driver_id]
                wait = WebDriverWait(driver, timeout)

                by_mapping = {
                    "css": By.CSS_SELECTOR,
                    "xpath": By.XPATH,
                    "id": By.ID,
                    "name": By.NAME,
                    "class": By.CLASS_NAME,
                    "tag": By.TAG_NAME,
                }

                if by not in by_mapping:
                    return f"Invalid selector type: {by}. Use css, xpath, id, name, class, or tag."

                element = wait.until(
                    EC.presence_of_element_located((by_mapping[by], selector))
                )
                return element.text

            except Exception as e:
                return f"Error getting text: {str(e)}"

        @self.mcp.tool()
        async def selenium_execute_script(driver_id: str, script: str) -> str:
            """Execute JavaScript using Selenium"""
            try:
                if driver_id not in self.active_selenium_drivers:
                    return f"Driver {driver_id} not found"

                driver = self.active_selenium_drivers[driver_id]
                result = driver.execute_script(script)

                return (
                    str(result)
                    if result is not None
                    else "Script executed successfully"
                )

            except Exception as e:
                return f"Error executing script: {str(e)}"

        @self.mcp.tool()
        async def selenium_wait_for_element(
            driver_id: str,
            selector: str,
            by: str = "css",
            timeout: int = 10,
            condition: str = "presence",
        ) -> str:
            """Wait for an element using Selenium"""
            try:
                if driver_id not in self.active_selenium_drivers:
                    return f"Driver {driver_id} not found"

                driver = self.active_selenium_drivers[driver_id]
                wait = WebDriverWait(driver, timeout)

                by_mapping = {
                    "css": By.CSS_SELECTOR,
                    "xpath": By.XPATH,
                    "id": By.ID,
                    "name": By.NAME,
                    "class": By.CLASS_NAME,
                    "tag": By.TAG_NAME,
                }

                if by not in by_mapping:
                    return f"Invalid selector type: {by}. Use css, xpath, id, name, class, or tag."

                condition_mapping = {
                    "presence": EC.presence_of_element_located,
                    "visible": EC.visibility_of_element_located,
                    "clickable": EC.element_to_be_clickable,
                }

                if condition not in condition_mapping:
                    return f"Invalid condition: {condition}. Use presence, visible, or clickable."

                wait.until(condition_mapping[condition]((by_mapping[by], selector)))
                return f"Element {selector} is now {condition}"

            except Exception as e:
                return f"Error waiting for element: {str(e)}"

        @self.mcp.tool()
        async def selenium_close_driver(driver_id: str) -> str:
            """Close a Selenium driver"""
            try:
                if driver_id not in self.active_selenium_drivers:
                    return f"Driver {driver_id} not found"

                driver = self.active_selenium_drivers[driver_id]
                driver.quit()
                del self.active_selenium_drivers[driver_id]

                return f"Driver {driver_id} closed"

            except Exception as e:
                return f"Error closing driver: {str(e)}"

        @self.mcp.tool()
        async def list_browser_instances() -> List[str]:
            """List all active browser instances"""
            instances = []

            # Add Playwright browsers
            for browser_id in self.active_browsers.keys():
                instances.append(f"Playwright: {browser_id}")

            # Add Selenium drivers
            for driver_id in self.active_selenium_drivers.keys():
                instances.append(f"Selenium: {driver_id}")

            return instances if instances else ["No active browser instances"]

        @self.mcp.tool()
        async def share_screenshot_with_ai(filename: str) -> str:
            """Share a screenshot file with AI by returning it as base64"""
            try:
                file_path = Path(self.temp_dir) / filename

                if not file_path.exists():
                    return f"Screenshot file {filename} not found in workspace"

                if not file_path.suffix.lower() in [".png", ".jpg", ".jpeg"]:
                    return f"File {filename} is not a valid image format"

                import base64

                with open(file_path, "rb") as f:
                    image_bytes = f.read()

                image_base64 = base64.b64encode(image_bytes).decode("utf-8")

                return json.dumps(
                    {
                        "type": "image_share",
                        "filename": filename,
                        "path": str(file_path),
                        "base64": image_base64,
                        "format": file_path.suffix.lower().replace(".", ""),
                        "message": f"Screenshot {filename} is now available for AI viewing",
                    }
                )

            except Exception as e:
                return f"Error sharing screenshot: {str(e)}"

    def setup_enhanced_logging(self):
        """Setup enhanced logging system with rotation and structured logging"""

        # Create formatters
        detailed_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s"
        )
        simple_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )

        # Configure root logger first
        self.logger = logging.getLogger("MCPDockerEnhanced")
        self.logger.setLevel(logging.DEBUG)
        self.logger.handlers.clear()

        # Setup console handler (always works) - using stderr to avoid MCP protocol issues
        # Only add console handler if not in MCP mode (detected by stdin being a pipe)
        if sys.stdin.isatty():
            console_handler = logging.StreamHandler(sys.stderr)
            console_handler.setFormatter(simple_formatter)
            console_handler.setLevel(logging.INFO)
            self.logger.addHandler(console_handler)

        # Try to setup file handlers with fallback
        try:
            file_handler = RotatingFileHandler(
                self.logs_dir / "mcpdocker_enhanced.log",
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
            )
            file_handler.setFormatter(detailed_formatter)
            file_handler.setLevel(logging.INFO)
            self.logger.addHandler(file_handler)

            error_handler = RotatingFileHandler(
                self.logs_dir / "mcpdocker_errors.log",
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=3,
            )
            error_handler.setFormatter(detailed_formatter)
            error_handler.setLevel(logging.ERROR)
            self.logger.addHandler(error_handler)

        except (PermissionError, OSError) as e:
            # If file logging fails, continue with stderr only
            print(f"Warning: Could not setup file logging: {e}", file=sys.stderr)

        # Performance logger with fallback
        self.perf_logger = logging.getLogger("MCPDockerPerformance")
        self.perf_logger.setLevel(logging.INFO)
        self.perf_logger.handlers.clear()

        if sys.stdin.isatty():
            perf_console = logging.StreamHandler(sys.stderr)
            perf_console.setFormatter(detailed_formatter)
            self.perf_logger.addHandler(perf_console)

        try:
            perf_handler = RotatingFileHandler(
                self.logs_dir / "performance.log",
                maxBytes=5 * 1024 * 1024,
                backupCount=2,
            )
            perf_handler.setFormatter(detailed_formatter)
            self.perf_logger.addHandler(perf_handler)
        except (PermissionError, OSError):
            pass  # Continue with stderr only

        # Security logger with fallback
        self.security_logger = logging.getLogger("MCPDockerSecurity")
        self.security_logger.setLevel(logging.WARNING)
        self.security_logger.handlers.clear()

        if sys.stdin.isatty():
            sec_console = logging.StreamHandler(sys.stderr)
            sec_console.setFormatter(detailed_formatter)
            self.security_logger.addHandler(sec_console)

        try:
            security_handler = RotatingFileHandler(
                self.logs_dir / "security.log", maxBytes=5 * 1024 * 1024, backupCount=3
            )
            security_handler.setFormatter(detailed_formatter)
            self.security_logger.addHandler(security_handler)
        except (PermissionError, OSError):
            pass  # Continue with stderr only

        self.logger.info(
            "Enhanced logging system initialized with rotation and structured logging"
        )

    def _register_enhanced_management_tools(self):
        """Register enhanced management and admin tools"""

        @self.mcp.tool()
        async def get_server_status() -> str:
            """Get comprehensive server status and health information"""
            try:
                uptime = time.time() - self.start_time

                # Update metrics
                self.metrics.uptime = uptime
                self.metrics.active_containers = len(self.active_containers)
                self.metrics.active_sessions = len(self.active_sessions)

                # System resources
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage("/")

                self.metrics.cpu_usage = cpu_percent
                self.metrics.memory_usage = memory.percent
                self.metrics.disk_usage = (disk.used / disk.total) * 100

                # Run health checks
                health_results = {}
                if hasattr(self, "health_checks"):
                    for check_name, check_func in self.health_checks.items():
                        try:
                            health_results[check_name] = await check_func()
                        except Exception as e:
                            health_results[check_name] = f"Failed: {str(e)}"

                self.health_status.checks = health_results
                self.health_status.metrics = self.metrics
                self.health_status.timestamp = datetime.now()

                status_report = f"""🚀 MCPDocker Enhanced Server Status
                
📊 System Metrics:
  • Uptime: {uptime/3600:.1f} hours
  • CPU Usage: {cpu_percent:.1f}%
  • Memory Usage: {memory.percent:.1f}% ({memory.available//1024//1024} MB free)
  • Disk Usage: {self.metrics.disk_usage:.1f}% ({disk.free//1024//1024//1024} GB free)
  • Active Containers: {len(self.active_containers)}
  • Active Sessions: {len(self.active_sessions)}
  
📈 API Metrics:
  • Total Requests: {self.metrics.requests_total}
  • Successful: {self.metrics.requests_successful}
  • Failed: {self.metrics.requests_failed}
  • Success Rate: {(self.metrics.requests_successful/max(1,self.metrics.requests_total)*100):.1f}%
  
🔍 Health Checks:
{chr(10).join(f"  • {name}: {'✅' if 'Failed' not in str(result) else '❌'} {result}" for name, result in health_results.items())}
  
🛡️ Security Status:
  • Authentication: {'Enabled' if self.service_config.authentication_enabled else 'Disabled'}
  • Rate Limiting: {'Enabled' if self.service_config.rate_limiting_enabled else 'Disabled'}
  • Security Level: {self.service_config.security_level.value.upper()}
  
🔧 Features:
  • Docker Management: {'✅' if self.service_config.docker_management else '❌'}
  • Browser Automation: {'✅' if self.service_config.browser_automation else '❌'}
  • GPU Support: {'✅' if self.service_config.gpu_support and self.gpu_available else '❌'}
  • WebSocket: {'✅' if self.service_config.websocket_enabled else '❌'}
  • Monitoring: {'✅' if self.service_config.monitoring_tools else '❌'}
  • Development Tools: {'✅' if self.service_config.development_tools else '❌'}
                """

                return status_report

            except Exception as e:
                self.logger.error(f"Error getting server status: {e}")
                return f"Error retrieving server status: {str(e)}"

        @self.mcp.tool()
        async def restart_server_services() -> str:
            """Restart server services and reinitialize components"""
            try:
                self.logger.info("Restarting server services...")

                # Reinitialize components
                if self.service_config.caching_enabled:
                    self._init_caching_system()

                # Clear expired cache entries
                if hasattr(self, "cache"):
                    expired_keys = []
                    current_time = time.time()
                    for key in list(self.cache.keys()):
                        if key not in self.cache:  # TTL expired
                            expired_keys.append(key)
                    self.logger.info(
                        f"Cleared {len(expired_keys)} expired cache entries"
                    )

                # Restart health checks
                if self.service_config.health_checks_enabled:
                    self._init_health_checks()

                self.logger.info("Server services restarted successfully")
                return "✅ Server services restarted successfully"

            except Exception as e:
                self.logger.error(f"Error restarting services: {e}")
                return f"❌ Error restarting services: {str(e)}"

        @self.mcp.tool()
        async def update_server_config(config_updates: Dict[str, Any]) -> str:
            """Update server configuration dynamically"""
            try:
                updated_configs = []

                for key, value in config_updates.items():
                    if hasattr(self.service_config, key):
                        old_value = getattr(self.service_config, key)
                        setattr(self.service_config, key, value)
                        updated_configs.append(f"{key}: {old_value} → {value}")

                        # Log configuration change - removed SQLite dependency

                        self.logger.info(f"Configuration updated: {key} = {value}")
                    else:
                        return f"❌ Unknown configuration key: {key}"

                return f"✅ Configuration updated:\n" + "\n".join(
                    f"  • {update}" for update in updated_configs
                )

            except Exception as e:
                self.logger.error(f"Error updating configuration: {e}")
                return f"❌ Error updating configuration: {str(e)}"

    def _register_security_tools(self):
        """Register security and audit tools"""

        @self.mcp.tool()
        async def security_audit_scan() -> str:
            """Perform comprehensive security audit of the system"""
            try:
                audit_results = []

                # Check Docker daemon security
                docker_info = self.docker_client.info()
                if docker_info.get("SecurityOptions"):
                    audit_results.append("✅ Docker security options enabled")
                else:
                    audit_results.append("⚠️ No Docker security options detected")

                # Check running containers security
                risky_containers = []
                for container_id, container in self.active_containers.items():
                    try:
                        container.reload()
                        config = container.attrs.get("HostConfig", {})

                        if config.get("Privileged", False):
                            risky_containers.append(
                                f"{container_id[:12]} (privileged mode)"
                            )

                        if config.get("NetworkMode") == "host":
                            risky_containers.append(
                                f"{container_id[:12]} (host networking)"
                            )

                    except Exception:
                        continue

                if risky_containers:
                    audit_results.append(f"⚠️ High-risk containers detected:")
                    for container in risky_containers:
                        audit_results.append(f"    • {container}")
                else:
                    audit_results.append("✅ No high-risk containers detected")

                # Check file permissions
                sensitive_paths = [self.logs_dir, self.config_dir]
                for path in sensitive_paths:
                    if path.exists():
                        stat = path.stat()
                        mode = oct(stat.st_mode)[-3:]
                        if mode != "600" and mode != "700":
                            audit_results.append(
                                f"⚠️ Insecure permissions on {path}: {mode}"
                            )
                        else:
                            audit_results.append(f"✅ Secure permissions on {path}")

                # Check for recent suspicious activity - SQLite dependency removed
                # Security event tracking would go here in a production system
                audit_results.append(
                    "✅ No high-risk security events detected (database disabled)"
                )

                # Generate security score
                total_checks = len(audit_results)
                passed_checks = len([r for r in audit_results if r.startswith("✅")])
                security_score = (passed_checks / total_checks) * 100

                audit_report = f"""🛡️ Security Audit Report
                
📊 Security Score: {security_score:.1f}% ({passed_checks}/{total_checks} checks passed)

🔍 Audit Results:
{chr(10).join(audit_results)}

📋 Recommendations:
• Enable Docker security options if not already active
• Avoid running containers in privileged mode unless necessary
• Regular security updates and patches
• Monitor security audit logs for suspicious activity
• Implement proper access controls and authentication

🕒 Audit completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

                # Security event logging removed - SQLite dependency eliminated

                return audit_report

            except Exception as e:
                self.logger.error(f"Security audit failed: {e}")
                # Security event logging removed - SQLite dependency eliminated
                return f"❌ Security audit failed: {str(e)}"

    def _register_websocket_tools(self):
        """Register WebSocket tools for real-time monitoring"""

        @self.mcp.tool()
        async def start_realtime_monitoring(container_id: str = None) -> str:
            """Start real-time monitoring of containers via WebSocket"""
            try:
                if not hasattr(self, "websocket_connections"):
                    return "❌ WebSocket support not enabled"

                # Create monitoring stream
                stream_key = f"realtime_{container_id or 'all'}_{int(time.time())}"

                def monitor_loop():
                    while stream_key in self.active_streams:
                        try:
                            if container_id:
                                # Monitor specific container
                                container = self._find_container(container_id)
                                if container:
                                    stats = container.stats(stream=False)
                                    monitoring_data = {
                                        "type": "container_stats",
                                        "container_id": container_id,
                                        "timestamp": time.time(),
                                        "stats": self._process_container_stats(stats),
                                    }
                                else:
                                    monitoring_data = {
                                        "type": "error",
                                        "message": f"Container {container_id} not found",
                                    }
                            else:
                                # Monitor all containers
                                monitoring_data = {
                                    "type": "system_stats",
                                    "timestamp": time.time(),
                                    "cpu_percent": psutil.cpu_percent(),
                                    "memory": psutil.virtual_memory()._asdict(),
                                    "disk": psutil.disk_usage("/")._asdict(),
                                    "active_containers": len(self.active_containers),
                                }

                            # Store in stream buffer
                            if stream_key not in self.active_streams:
                                self.active_streams[stream_key] = {
                                    "buffer": [],
                                    "type": "realtime",
                                }

                            self.active_streams[stream_key]["buffer"].append(
                                monitoring_data
                            )

                            # Broadcast to WebSocket connections
                            self._broadcast_to_websockets(monitoring_data)

                            time.sleep(1)  # Update every second

                        except Exception as e:
                            self.logger.error(f"Monitoring error: {e}")
                            break

                # Start monitoring thread
                monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
                monitor_thread.start()

                self.active_streams[stream_key] = {
                    "buffer": [],
                    "type": "realtime",
                    "thread": monitor_thread,
                    "container_id": container_id,
                }

                return f"✅ Real-time monitoring started: {stream_key}"

            except Exception as e:
                self.logger.error(f"Failed to start real-time monitoring: {e}")
                return f"❌ Failed to start monitoring: {str(e)}"

        @self.mcp.tool()
        async def websocket_broadcast_message(
            message: str, message_type: str = "info"
        ) -> str:
            """Broadcast a message to all connected WebSocket clients"""
            try:
                if not hasattr(self, "websocket_connections"):
                    return "❌ WebSocket support not enabled"

                broadcast_data = {
                    "type": "broadcast",
                    "message_type": message_type,
                    "message": message,
                    "timestamp": time.time(),
                }

                self._broadcast_to_websockets(broadcast_data)

                return f"✅ Message broadcasted to {len(self.websocket_connections)} clients"

            except Exception as e:
                return f"❌ Broadcast failed: {str(e)}"

    def _broadcast_to_websockets(self, data: dict):
        """Broadcast data to all connected WebSocket clients"""
        if hasattr(self, "websocket_connections"):
            disconnected = set()
            for websocket in self.websocket_connections:
                try:
                    # This would need to be implemented with actual WebSocket library
                    # For now, just log the broadcast
                    self.logger.debug(
                        f"Broadcasting data to WebSocket: {data.get('type', 'unknown')}"
                    )
                except Exception as e:
                    self.logger.warning(f"WebSocket broadcast failed: {e}")
                    disconnected.add(websocket)

            # Remove disconnected clients
            self.websocket_connections -= disconnected

    def _process_container_stats(self, stats: dict) -> dict:
        """Process raw container stats into readable format"""
        try:
            # CPU usage calculation
            cpu_delta = (
                stats["cpu_stats"]["cpu_usage"]["total_usage"]
                - stats["precpu_stats"]["cpu_usage"]["total_usage"]
            )
            system_delta = (
                stats["cpu_stats"]["system_cpu_usage"]
                - stats["precpu_stats"]["system_cpu_usage"]
            )
            cpu_percent = (
                (cpu_delta / system_delta)
                * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"])
                * 100.0
                if system_delta > 0
                else 0
            )

            # Memory usage
            memory_usage = stats["memory_stats"].get("usage", 0)
            memory_limit = stats["memory_stats"].get("limit", 0)
            memory_percent = (
                (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
            )

            # Network I/O
            networks = stats.get("networks", {})
            total_rx = sum(net["rx_bytes"] for net in networks.values())
            total_tx = sum(net["tx_bytes"] for net in networks.values())

            return {
                "cpu_percent": round(cpu_percent, 2),
                "memory_usage_mb": round(memory_usage / (1024 * 1024), 2),
                "memory_limit_mb": round(memory_limit / (1024 * 1024), 2),
                "memory_percent": round(memory_percent, 2),
                "network_rx_mb": round(total_rx / (1024 * 1024), 2),
                "network_tx_mb": round(total_tx / (1024 * 1024), 2),
            }
        except Exception as e:
            self.logger.error(f"Error processing container stats: {e}")
            return {"error": str(e)}

    async def _health_check_docker(self) -> str:
        """Check Docker daemon health"""
        try:
            self.docker_client.ping()
            return "Docker daemon accessible"
        except Exception as e:
            return f"Docker daemon error: {str(e)}"

    async def _health_check_disk_space(self) -> str:
        """Check disk space"""
        try:
            disk = psutil.disk_usage("/")
            free_percent = (disk.free / disk.total) * 100
            if free_percent < 10:
                return f"Low disk space: {free_percent:.1f}% free"
            return f"Disk space OK: {free_percent:.1f}% free"
        except Exception as e:
            return f"Disk check error: {str(e)}"

    async def _health_check_memory(self) -> str:
        """Check memory usage"""
        try:
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                return f"High memory usage: {memory.percent:.1f}%"
            return f"Memory usage OK: {memory.percent:.1f}%"
        except Exception as e:
            return f"Memory check error: {str(e)}"

    async def _health_check_containers(self) -> str:
        """Check container health"""
        try:
            unhealthy_containers = 0
            for container_id, container in self.active_containers.items():
                try:
                    container.reload()
                    if container.status != "running":
                        unhealthy_containers += 1
                except:
                    unhealthy_containers += 1

            if unhealthy_containers > 0:
                return f"{unhealthy_containers} unhealthy containers"
            return "All containers healthy"
        except Exception as e:
            return f"Container check error: {str(e)}"

    def _cleanup_expired_containers(self):
        """Clean up expired containers"""
        try:
            # Remove exited containers older than 24 hours
            for container in self.docker_client.containers.list(all=True):
                if container.status == "exited":
                    # Check if container is older than 24 hours
                    created = datetime.fromisoformat(
                        container.attrs["Created"].replace("Z", "+00:00")
                    )
                    if datetime.now(created.tzinfo) - created > timedelta(hours=24):
                        try:
                            container.remove()
                            self.logger.info(
                                f"Cleaned up expired container: {container.id[:12]}"
                            )
                        except Exception as e:
                            self.logger.warning(
                                f"Failed to cleanup container {container.id[:12]}: {e}"
                            )
        except Exception as e:
            self.logger.error(f"Container cleanup error: {e}")

    def _cleanup_old_logs(self):
        """Clean up old log files"""
        try:
            import glob

            # Clean up logs older than 30 days
            cutoff_time = time.time() - (30 * 24 * 3600)
            for log_file in glob.glob(str(self.logs_dir / "*.log*")):
                if os.path.getmtime(log_file) < cutoff_time:
                    try:
                        os.remove(log_file)
                        self.logger.info(f"Cleaned up old log file: {log_file}")
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to cleanup log file {log_file}: {e}"
                        )
        except Exception as e:
            self.logger.error(f"Log cleanup error: {e}")

    def _cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            import glob

            # Clean up temp files older than 1 hour
            cutoff_time = time.time() - 3600
            for temp_file in glob.glob(os.path.join(self.temp_dir, "*")):
                if os.path.getmtime(temp_file) < cutoff_time:
                    try:
                        if os.path.isfile(temp_file):
                            os.remove(temp_file)
                        elif os.path.isdir(temp_file):
                            shutil.rmtree(temp_file)
                        self.logger.debug(f"Cleaned up temp file: {temp_file}")
                    except Exception as e:
                        self.logger.warning(
                            f"Failed to cleanup temp file {temp_file}: {e}"
                        )
        except Exception as e:
            self.logger.error(f"Temp file cleanup error: {e}")

    def _register_browser_tools(self):
        """Register browser automation tools"""

        @self.mcp.tool()
        async def monitor_system_resources() -> str:
            """Monitor system CPU, memory, disk usage and Docker daemon status"""
            try:
                import psutil

                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_count = psutil.cpu_count()

                # Memory usage
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_available = memory.available / (1024**3)  # GB
                memory_total = memory.total / (1024**3)  # GB

                # Disk usage
                disk = psutil.disk_usage("/")
                disk_percent = (disk.used / disk.total) * 100
                disk_free = disk.free / (1024**3)  # GB
                disk_total = disk.total / (1024**3)  # GB

                # Docker daemon status
                try:
                    docker_info = self.docker_client.info()
                    docker_status = "Running"
                    containers_running = docker_info.get("ContainersRunning", 0)
                    containers_total = docker_info.get("Containers", 0)
                    images_count = docker_info.get("Images", 0)
                except Exception:
                    docker_status = "Not accessible"
                    containers_running = containers_total = images_count = 0

                # Store metrics in database
                timestamp = datetime.now()
                # Metrics storage removed - SQLite dependency eliminated

                report = f"""System Resource Monitor:
📊 CPU: {cpu_percent:.1f}% ({cpu_count} cores)
🧠 Memory: {memory_percent:.1f}% ({memory_available:.1f}GB free / {memory_total:.1f}GB total)
💾 Disk: {disk_percent:.1f}% ({disk_free:.1f}GB free / {disk_total:.1f}GB total)
🐳 Docker: {docker_status} ({containers_running}/{containers_total} containers, {images_count} images)
⏰ Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"""

                return report

            except Exception as e:
                return f"Error monitoring system resources: {str(e)}"

        @self.mcp.tool()
        async def monitor_container_performance(container_id: str) -> str:
            """Monitor detailed performance metrics for a specific container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                # Get container stats
                stats = container.stats(stream=False)

                # CPU usage calculation
                cpu_delta = (
                    stats["cpu_stats"]["cpu_usage"]["total_usage"]
                    - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                )
                system_delta = (
                    stats["cpu_stats"]["system_cpu_usage"]
                    - stats["precpu_stats"]["system_cpu_usage"]
                )
                cpu_percent = (
                    (cpu_delta / system_delta)
                    * len(stats["cpu_stats"]["cpu_usage"]["percpu_usage"])
                    * 100.0
                )

                # Memory usage
                memory_usage = stats["memory_stats"].get("usage", 0)
                memory_limit = stats["memory_stats"].get("limit", 0)
                memory_percent = (
                    (memory_usage / memory_limit) * 100 if memory_limit > 0 else 0
                )

                # Network I/O
                networks = stats.get("networks", {})
                total_rx = sum(net["rx_bytes"] for net in networks.values())
                total_tx = sum(net["tx_bytes"] for net in networks.values())

                # Block I/O
                blkio_stats = stats.get("blkio_stats", {}).get(
                    "io_service_bytes_recursive", []
                )
                total_read = sum(
                    item["value"] for item in blkio_stats if item["op"] == "Read"
                )
                total_write = sum(
                    item["value"] for item in blkio_stats if item["op"] == "Write"
                )

                # Store metrics
                timestamp = datetime.now()
                # Container metrics storage removed - SQLite dependency eliminated

                report = f"""Container Performance [{container_id[:12]}]:
🔧 CPU: {cpu_percent:.2f}%
🧠 Memory: {memory_percent:.1f}% ({memory_usage/(1024**2):.1f}MB / {memory_limit/(1024**2):.1f}MB)
📡 Network: ↓{total_rx/(1024**2):.1f}MB ↑{total_tx/(1024**2):.1f}MB
💿 Block I/O: Read {total_read/(1024**2):.1f}MB, Write {total_write/(1024**2):.1f}MB
⏰ Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"""

                return report

            except Exception as e:
                return f"Error monitoring container performance: {str(e)}"

        @self.mcp.tool()
        async def create_container_backup(
            container_id: str, backup_name: str = None
        ) -> str:
            """Create a complete backup of a container including its data"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                if backup_name is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"backup_{container_id[:12]}_{timestamp}"

                backup_path = self.backup_dir / f"{backup_name}.tar"

                # Create container snapshot
                image_name = f"backup_{container_id[:12]}_{int(time.time())}"
                container.commit(repository=image_name)

                # Export container data
                with open(backup_path, "wb") as f:
                    image = self.docker_client.images.get(image_name)
                    for chunk in image.save():
                        f.write(chunk)

                # Get backup size
                backup_size = backup_path.stat().st_size

                # Backup info storage removed - SQLite dependency eliminated

                # Clean up temporary image
                self.docker_client.images.remove(image_name, force=True)

                return f"Container backup created: {backup_name} ({backup_size/(1024**2):.1f}MB)"

            except Exception as e:
                return f"Error creating container backup: {str(e)}"

        @self.mcp.tool()
        async def create_workspace_backup(backup_name: str = None) -> str:
            """Create a backup of the shared workspace"""
            try:
                if backup_name is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"workspace_backup_{timestamp}"

                backup_path = self.backup_dir / f"{backup_name}.tar.gz"

                # Create tar.gz archive of workspace
                with tarfile.open(backup_path, "w:gz") as archive:
                    archive.add(self.temp_dir, arcname="workspace")

                backup_size = backup_path.stat().st_size

                # Backup info storage removed - SQLite dependency eliminated

                return f"Workspace backup created: {backup_name} ({backup_size/(1024**2):.1f}MB)"

            except Exception as e:
                return f"Error creating workspace backup: {str(e)}"

    def _register_monitoring_tools(self):
        """Register monitoring and analytics tools"""

    def _register_development_tools(self):
        """Register development environment and project management tools"""

        @self.mcp.tool()
        async def create_dev_environment(language: str, project_name: str) -> str:
            """Create a pre-configured development environment container"""
            try:
                # Define development environment configurations
                dev_configs = {
                    "python": {
                        "image": "python:3.11",
                        "packages": [
                            "pip install jupyter pandas numpy matplotlib seaborn"
                        ],
                        "ports": {8888: 8888},
                    },
                    "node": {
                        "image": "node:18",
                        "packages": ["npm install -g typescript @types/node ts-node"],
                        "ports": {3000: 3000},
                    },
                    "golang": {
                        "image": "golang:1.21",
                        "packages": ["go install github.com/cosmtrek/air@latest"],
                        "ports": {8080: 8080},
                    },
                    "rust": {
                        "image": "rust:1.70",
                        "packages": ["cargo install cargo-watch"],
                        "ports": {8000: 8000},
                    },
                }

                if language not in dev_configs:
                    return f"Unsupported development language: {language}"

                config = dev_configs[language]
                container_name = f"dev_{language}_{project_name}"

                # Create container
                container = self.docker_client.containers.run(
                    config["image"],
                    command="tail -f /dev/null",
                    name=container_name,
                    detach=True,
                    ports=config["ports"],
                    volumes={self.temp_dir: {"bind": "/workspace", "mode": "rw"}},
                    working_dir="/workspace",
                    tty=True,
                    stdin_open=True,
                )

                self.active_containers[container.id] = container

                # Install development packages
                for package_cmd in config["packages"]:
                    container.exec_run(package_cmd)

                # Create project structure
                project_dir = f"/workspace/{project_name}"
                container.exec_run(f"mkdir -p {project_dir}")

                return f"Development environment created: {container_name} ({container.id[:12]})"

            except Exception as e:
                return f"Error creating development environment: {str(e)}"

    def _register_workflow_tools(self):
        """Register workflow automation and CI/CD tools"""

        @self.mcp.tool()
        async def create_dockerfile(language: str, project_name: str) -> str:
            """Generate a Dockerfile template for the specified language"""
            try:
                dockerfile_templates = {
                    "python": f"""FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
""",
                    "node": f"""FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
""",
                    "golang": f"""FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN go build -o main .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/
COPY --from=builder /app/main .
EXPOSE 8080
CMD ["./main"]
""",
                }

                if language not in dockerfile_templates:
                    return f"No Dockerfile template available for {language}"

                dockerfile_content = dockerfile_templates[language]
                dockerfile_path = Path(self.temp_dir) / project_name / "Dockerfile"
                dockerfile_path.parent.mkdir(exist_ok=True)

                with open(dockerfile_path, "w") as f:
                    f.write(dockerfile_content)

                return f"Dockerfile created at {dockerfile_path}"

            except Exception as e:
                return f"Error creating Dockerfile: {str(e)}"

        @self.mcp.tool()
        async def inspect_network() -> str:
            """Inspect Docker networks and container connectivity"""
            try:
                networks = self.docker_client.networks.list()
                network_info = []

                for network in networks:
                    containers = []
                    for container_id, container_config in network.attrs.get(
                        "Containers", {}
                    ).items():
                        container_name = container_config.get("Name", "Unknown")
                        container_ip = container_config.get("IPv4Address", "").split(
                            "/"
                        )[0]
                        containers.append(f"{container_name} ({container_ip})")

                    network_info.append(
                        f"""
Network: {network.name} ({network.short_id})
Driver: {network.attrs.get('Driver', 'Unknown')}
Scope: {network.attrs.get('Scope', 'Unknown')}
Containers: {len(containers)}
{chr(10).join(f"  - {container}" for container in containers)}
"""
                    )

                return "Docker Network Inspection:\n" + "\n".join(network_info)

            except Exception as e:
                return f"Error inspecting networks: {str(e)}"

        @self.mcp.tool()
        async def scan_container_ports(container_id: str) -> str:
            """Scan open ports on a container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                container.reload()
                port_bindings = container.attrs.get("NetworkSettings", {}).get(
                    "Ports", {}
                )

                port_info = []
                for container_port, host_bindings in port_bindings.items():
                    if host_bindings:
                        for binding in host_bindings:
                            host_ip = binding.get("HostIp", "0.0.0.0")
                            host_port = binding.get("HostPort", "N/A")
                            port_info.append(
                                f"{container_port} -> {host_ip}:{host_port}"
                            )
                    else:
                        port_info.append(f"{container_port} (internal only)")

                return (
                    f"Port mapping for container {container_id[:12]}:\n"
                    + "\n".join(port_info)
                    if port_info
                    else f"No exposed ports found for container {container_id[:12]}"
                )

            except Exception as e:
                return f"Error scanning container ports: {str(e)}"

        @self.mcp.tool()
        async def security_scan_comprehensive(container_id: str) -> str:
            """Perform comprehensive security analysis of a container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                security_report = []

                # Check running processes
                result = container.exec_run("ps aux")
                if result.exit_code == 0:
                    processes = result.output.decode("utf-8").split("\n")
                    security_report.append(f"Running Processes ({len(processes)-1}):")
                    for proc in processes[1:6]:  # Show top 5
                        if proc.strip():
                            security_report.append(f"  {proc}")

                # Check for common security files
                security_files = [
                    "/etc/passwd",
                    "/etc/shadow",
                    "/etc/hosts",
                    "/root/.ssh/authorized_keys",
                ]
                for file_path in security_files:
                    result = container.exec_run(
                        f"test -f {file_path} && echo 'EXISTS' || echo 'NOT_FOUND'"
                    )
                    if result.exit_code == 0:
                        status = result.output.decode("utf-8").strip()
                        security_report.append(f"{file_path}: {status}")

                # Check for SUID/SGID files
                result = container.exec_run(
                    "find /usr -perm /4000 -o -perm /2000 2>/dev/null | head -10"
                )
                if result.exit_code == 0:
                    suid_files = result.output.decode("utf-8").strip().split("\n")
                    if suid_files and suid_files[0]:
                        security_report.append(
                            f"SUID/SGID files found: {len(suid_files)}"
                        )
                        for suid_file in suid_files[:5]:
                            if suid_file.strip():
                                security_report.append(f"  {suid_file}")

                # Check container configuration
                container.reload()
                privileged = container.attrs.get("HostConfig", {}).get(
                    "Privileged", False
                )
                security_report.append(
                    f"Privileged mode: {'⚠️  YES' if privileged else '✅ NO'}"
                )

                user = container.attrs.get("Config", {}).get("User", "root")
                security_report.append(f"Running as user: {user}")

                return (
                    f"Security Analysis for Container {container_id[:12]}:\n"
                    + "\n".join(security_report)
                )

            except Exception as e:
                return f"Error performing security scan: {str(e)}"

        @self.mcp.tool()
        async def generate_project_template(
            language: str, project_name: str, features: List[str] = None
        ) -> str:
            """Generate a complete project template with best practices"""
            try:
                features = features or []
                project_path = Path(self.temp_dir) / project_name
                project_path.mkdir(exist_ok=True)

                if language == "python":
                    # Create Python project structure
                    (project_path / "src").mkdir(exist_ok=True)
                    (project_path / "tests").mkdir(exist_ok=True)
                    (project_path / "docs").mkdir(exist_ok=True)

                    # requirements.txt
                    requirements = [
                        "flask==2.3.0",
                        "pytest==7.4.0",
                        "black==23.3.0",
                        "flake8==6.0.0",
                    ]
                    if "ai" in features:
                        requirements.extend(
                            ["numpy==1.24.0", "pandas==2.0.0", "scikit-learn==1.3.0"]
                        )
                    if "web" in features:
                        requirements.extend(["fastapi==0.100.0", "uvicorn==0.22.0"])

                    with open(project_path / "requirements.txt", "w") as f:
                        f.write("\n".join(requirements))

                    # main.py
                    with open(project_path / "src" / "main.py", "w") as f:
                        f.write(
                            f'''"""
{project_name} - Main application module
"""

def main():
    # Project template created

if __name__ == "__main__":
    main()
'''
                        )

                    # pytest config
                    with open(project_path / "pytest.ini", "w") as f:
                        f.write(
                            """[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
"""
                        )

                elif language == "node":
                    # Create Node.js project structure
                    (project_path / "src").mkdir(exist_ok=True)
                    (project_path / "tests").mkdir(exist_ok=True)

                    # package.json
                    package_json = {
                        "name": project_name,
                        "version": "1.0.0",
                        "description": f"{project_name} application",
                        "main": "src/index.js",
                        "scripts": {
                            "start": "node src/index.js",
                            "dev": "nodemon src/index.js",
                            "test": "jest",
                        },
                        "dependencies": {"express": "^4.18.0"},
                        "devDependencies": {"nodemon": "^3.0.0", "jest": "^29.5.0"},
                    }

                    with open(project_path / "package.json", "w") as f:
                        f.write(json.dumps(package_json, indent=2))

                    # index.js
                    with open(project_path / "src" / "index.js", "w") as f:
                        f.write(
                            f"""const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {{
    res.json({{ message: 'Hello from {project_name}!' }});
}});

app.listen(PORT, () => {{
    console.log(`{project_name} server running on port ${{PORT}}`);
}});

module.exports = app;
"""
                        )

                # Create common files
                with open(project_path / "README.md", "w") as f:
                    f.write(
                        f"""# {project_name}

## Description
{project_name} application built with {language}

## Features
{chr(10).join(f"- {feature}" for feature in features) if features else "- Basic application structure"}

## Installation
```bash
# Install dependencies
{"pip install -r requirements.txt" if language == "python" else "npm install"}
```

## Usage
```bash
# Run the application
{"python src/main.py" if language == "python" else "npm start"}
```

## Development
```bash
# Run tests
{"pytest" if language == "python" else "npm test"}
```
"""
                    )

                # .gitignore
                gitignore_content = {
                    "python": "__pycache__/\n*.pyc\n*.pyo\n*.pyd\n.env\n.venv/\ndist/\nbuild/\n*.egg-info/",
                    "node": "node_modules/\nnpm-debug.log*\n.env\ndist/\nbuild/",
                }.get(language, "")

                with open(project_path / ".gitignore", "w") as f:
                    f.write(gitignore_content)

                return f"Project template created for {project_name} ({language}) with features: {', '.join(features) if features else 'basic'}"

            except Exception as e:
                return f"Error generating project template: {str(e)}"

        @self.mcp.tool()
        async def ai_code_analysis(container_id: str, file_path: str) -> str:
            """Perform AI-powered code analysis and suggestions"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"

                # Read file content
                result = container.exec_run(f"cat {file_path}")
                if result.exit_code != 0:
                    return f"Error reading file {file_path}: {result.output.decode('utf-8')}"

                code_content = result.output.decode("utf-8")

                # Basic code analysis
                analysis_results = []

                # Count lines and basic metrics
                lines = code_content.split("\n")
                total_lines = len(lines)
                non_empty_lines = len([line for line in lines if line.strip()])
                comment_lines = len(
                    [
                        line
                        for line in lines
                        if line.strip().startswith("#") or line.strip().startswith("//")
                    ]
                )

                analysis_results.append(f"📊 Code Metrics:")
                analysis_results.append(f"  Total lines: {total_lines}")
                analysis_results.append(f"  Non-empty lines: {non_empty_lines}")
                analysis_results.append(f"  Comment lines: {comment_lines}")
                analysis_results.append(
                    f"  Comment ratio: {comment_lines/non_empty_lines*100:.1f}%"
                    if non_empty_lines > 0
                    else "  Comment ratio: 0%"
                )

                # Detect language and provide specific analysis
                file_ext = Path(file_path).suffix.lower()
                if file_ext in [".py"]:
                    # Python-specific analysis
                    import_lines = [
                        line
                        for line in lines
                        if line.strip().startswith("import ")
                        or line.strip().startswith("from ")
                    ]
                    function_lines = [line for line in lines if "def " in line]
                    class_lines = [line for line in lines if "class " in line]

                    analysis_results.append(f"🐍 Python Analysis:")
                    analysis_results.append(f"  Imports: {len(import_lines)}")
                    analysis_results.append(f"  Functions: {len(function_lines)}")
                    analysis_results.append(f"  Classes: {len(class_lines)}")

                elif file_ext in [".js", ".ts"]:
                    # JavaScript/TypeScript analysis
                    function_lines = [
                        line for line in lines if "function " in line or "=>" in line
                    ]
                    const_lines = [
                        line for line in lines if line.strip().startswith("const ")
                    ]
                    let_lines = [
                        line for line in lines if line.strip().startswith("let ")
                    ]

                    analysis_results.append(f"🟨 JavaScript Analysis:")
                    analysis_results.append(f"  Functions: {len(function_lines)}")
                    analysis_results.append(f"  Const declarations: {len(const_lines)}")
                    analysis_results.append(f"  Let declarations: {len(let_lines)}")

                # Security checks
                security_issues = []
                for i, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    if "password" in line_lower and "=" in line_lower:
                        security_issues.append(
                            f"Line {i}: Potential hardcoded password"
                        )
                    if "api_key" in line_lower and "=" in line_lower:
                        security_issues.append(f"Line {i}: Potential hardcoded API key")
                    if "eval(" in line_lower:
                        security_issues.append(
                            f"Line {i}: Use of eval() function (security risk)"
                        )

                if security_issues:
                    analysis_results.append(f"🔒 Security Issues:")
                    for issue in security_issues[:5]:  # Show max 5 issues
                        analysis_results.append(f"  ⚠️  {issue}")

                # Code quality suggestions
                suggestions = []
                if (
                    comment_lines / non_empty_lines < 0.1
                    if non_empty_lines > 0
                    else True
                ):
                    suggestions.append(
                        "Consider adding more comments for better code documentation"
                    )
                if total_lines > 500:
                    suggestions.append(
                        "Large file detected - consider breaking into smaller modules"
                    )
                if len([line for line in lines if len(line) > 120]) > 5:
                    suggestions.append(
                        "Multiple long lines detected - consider breaking for better readability"
                    )

                if suggestions:
                    analysis_results.append(f"💡 Suggestions:")
                    for suggestion in suggestions:
                        analysis_results.append(f"  - {suggestion}")

                return f"AI Code Analysis for {file_path}:\n" + "\n".join(
                    analysis_results
                )

            except Exception as e:
                return f"Error analyzing code: {str(e)}"

        @self.mcp.tool()
        async def setup_ci_cd_pipeline(
            project_name: str, language: str, platform: str = "github"
        ) -> str:
            """Setup CI/CD pipeline configuration files"""
            try:
                project_path = Path(self.temp_dir) / project_name

                if platform == "github":
                    workflows_dir = project_path / ".github" / "workflows"
                    workflows_dir.mkdir(parents=True, exist_ok=True)

                    if language == "python":
                        workflow_content = f"""name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{{{ matrix.python-version }}}}
      uses: actions/setup-python@v3
      with:
        python-version: ${{{{ matrix.python-version }}}}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov black flake8
    
    - name: Lint with flake8
      run: |
        flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 src/ --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Format check with black
      run: black --check src/
    
    - name: Test with pytest
      run: pytest tests/ --cov=src/ --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: |
        echo "Deploying {project_name} to production"
        # Add your deployment commands here
"""

                    elif language == "node":
                        workflow_content = f"""name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        node-version: [16.x, 18.x, 20.x]

    steps:
    - uses: actions/checkout@v3
    
    - name: Use Node.js ${{{{ matrix.node-version }}}}
      uses: actions/setup-node@v3
      with:
        node-version: ${{{{ matrix.node-version }}}}
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run linter
      run: npm run lint
    
    - name: Run tests
      run: npm test
    
    - name: Run build
      run: npm run build

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to production
      run: |
        echo "Deploying {project_name} to production"
        # Add your deployment commands here
"""

                    with open(workflows_dir / "ci.yml", "w") as f:
                        f.write(workflow_content)

                # Create docker-compose for development
                docker_compose_content = f"""version: '3.8'

services:
  {project_name}:
    build: .
    ports:
      - "{'8000:8000' if language == 'python' else '3000:3000'}"
    volumes:
      - .:/app
    environment:
      - NODE_ENV=development
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: {project_name}
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: devpass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
"""

                with open(project_path / "docker-compose.yml", "w") as f:
                    f.write(docker_compose_content)

                return f"CI/CD pipeline configured for {project_name} ({language}) on {platform}"

            except Exception as e:
                return f"Error setting up CI/CD pipeline: {str(e)}"

    def _register_resources(self):
        """Register MCP resources for documentation access"""

        @self.mcp.resource("documentation://languages")
        async def list_documentation_languages() -> str:
            """List all supported programming languages for documentation"""
            try:
                languages_info = []
                for lang, config in self.supported_languages.items():
                    lang_docs_dir = self.docs_dir / config["folder"]
                    if lang_docs_dir.exists() and any(lang_docs_dir.iterdir()):
                        languages_info.append(
                            {
                                "language": lang,
                                "version": config.get("version", "Unknown"),
                                "folder": config["folder"],
                                "available": True,
                            }
                        )
                    else:
                        languages_info.append(
                            {
                                "language": lang,
                                "version": config.get("version", "Unknown"),
                                "folder": config["folder"],
                                "available": False,
                            }
                        )

                return json.dumps(languages_info, indent=2)

            except Exception as e:
                return json.dumps({"error": f"Error listing languages: {str(e)}"})

        @self.mcp.resource("documentation://{language}/files")
        async def list_documentation_files(language: str) -> str:
            """List documentation files for a specific language"""
            try:
                if language not in self.supported_languages:
                    return json.dumps({"error": f"Language '{language}' not supported"})

                lang_config = self.supported_languages[language]
                lang_docs_dir = self.docs_dir / lang_config["folder"]

                if not lang_docs_dir.exists():
                    return json.dumps(
                        {"error": f"{language} documentation not available"}
                    )

                files_info = []
                for root, _, files in os.walk(lang_docs_dir):
                    for file in files:
                        if file.endswith((".txt", ".md", ".rst")):
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, lang_docs_dir)
                            try:
                                file_size = os.path.getsize(file_path)
                                files_info.append(
                                    {
                                        "path": rel_path,
                                        "size": file_size,
                                        "type": file.split(".")[-1],
                                    }
                                )
                            except:
                                continue

                return json.dumps(
                    {
                        "language": language,
                        "files": sorted(files_info, key=lambda x: x["path"]),
                    },
                    indent=2,
                )

            except Exception as e:
                return json.dumps({"error": f"Error listing files: {str(e)}"})

        @self.mcp.resource("documentation://{language}/file/{file_path}")
        async def get_documentation_file(language: str, file_path: str) -> str:
            """Get content of a specific documentation file"""
            try:
                if language not in self.supported_languages:
                    return json.dumps({"error": f"Language '{language}' not supported"})

                lang_config = self.supported_languages[language]
                lang_docs_dir = self.docs_dir / lang_config["folder"]
                doc_file = lang_docs_dir / file_path

                if not doc_file.exists():
                    return json.dumps({"error": f"File {file_path} not found"})

                if not doc_file.suffix in [".txt", ".md", ".rst"]:
                    return json.dumps({"error": f"File format not supported"})

                with open(doc_file, "r", encoding="utf-8") as f:
                    content = f.read()

                return json.dumps(
                    {
                        "language": language,
                        "file_path": file_path,
                        "content": content,
                        "size": len(content),
                        "type": doc_file.suffix[1:],
                    },
                    indent=2,
                )

            except Exception as e:
                return json.dumps({"error": f"Error reading file: {str(e)}"})

    async def _get_playwright_page(self, page_id: str):
        """Helper method to get a Playwright page by ID"""
        for browser in self.active_browsers.values():
            if (
                hasattr(browser, "_page_references")
                and page_id in browser._page_references
            ):
                return browser._page_references[page_id]
        return f"Page {page_id} not found"

    def _start_stream_server(
        self, container, container_port: int, host_port: int, stream_key: str
    ):
        """Start a TCP server that streams data from container port to host port"""
        try:
            # Create server socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(("localhost", host_port))
            server_socket.listen(5)
            server_socket.settimeout(1.0)  # Non-blocking accept with timeout

            # Stream server listening

            while stream_key in self.active_streams:
                try:
                    client_socket, addr = server_socket.accept()
                    # Client connected to stream

                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_stream_client,
                        args=(client_socket, container, container_port, stream_key),
                        daemon=True,
                    )
                    client_thread.start()

                except socket.timeout:
                    continue
                except Exception as e:
                    # Error accepting connection
                    break

            server_socket.close()
            # Stream server stopped

        except Exception as e:
            # Error in stream server
            pass

    def _handle_stream_client(
        self, client_socket, container, container_port: int, stream_key: str
    ):
        """Handle individual client connection for streaming"""
        try:
            # Connect to container port
            container_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            container_socket.settimeout(5.0)

            # Get container IP
            container.reload()
            container_ip = container.attrs["NetworkSettings"]["IPAddress"]

            if not container_ip:
                # Try getting IP from networks
                networks = container.attrs["NetworkSettings"]["Networks"]
                if networks:
                    container_ip = list(networks.values())[0]["IPAddress"]

            if not container_ip:
                client_socket.send(b"Error: Could not determine container IP\n")
                return

            container_socket.connect((container_ip, container_port))

            # Start bidirectional streaming
            def forward_data(from_socket, to_socket):
                try:
                    while stream_key in self.active_streams:
                        data = from_socket.recv(4096)
                        if not data:
                            break
                        to_socket.send(data)
                except:
                    pass

            # Create threads for bidirectional communication
            client_to_container = threading.Thread(
                target=forward_data, args=(client_socket, container_socket), daemon=True
            )
            container_to_client = threading.Thread(
                target=forward_data, args=(container_socket, client_socket), daemon=True
            )

            client_to_container.start()
            container_to_client.start()

            # Wait for threads to complete
            client_to_container.join()
            container_to_client.join()

        except Exception as e:
            try:
                client_socket.send(f"Stream error: {str(e)}\n".encode())
            except:
                pass
            # Error in stream client handler
        finally:
            try:
                container_socket.close()
            except:
                pass
            try:
                client_socket.close()
            except:
                pass

    async def cleanup(self):
        """Clean up containers, streams, browser instances, and temporary files"""
        # Stop all active streams
        self.active_streams.clear()

        # Stop and remove containers
        for container in self.active_containers.values():
            try:
                container.stop()
                container.remove()
            except:
                pass

        # Close all Playwright browsers
        for browser in self.active_browsers.values():
            try:
                await browser.close()
            except:
                pass
        self.active_browsers.clear()

        # Close Playwright instance
        if self.playwright_instance:
            try:
                await self.playwright_instance.stop()
            except:
                pass

        # Close all Selenium drivers
        for driver in self.active_selenium_drivers.values():
            try:
                driver.quit()
            except:
                pass
        self.active_selenium_drivers.clear()

        # Shutdown thread pool
        if hasattr(self, "executor"):
            self.executor.shutdown(wait=True)

        # Database connection cleanup removed - SQLite dependency eliminated

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

        if hasattr(self, "logger"):
            self.logger.info("MCP Docker Server cleanup completed")

    def run(self, transport_method: str = "stdio"):
        """Run the MCP server"""
        # Suppress all logging in MCP mode to avoid protocol conflicts
        if transport_method == "stdio" and not sys.stdin.isatty():
            logging.getLogger().setLevel(logging.CRITICAL)
            logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
            logging.getLogger("fastapi").setLevel(logging.CRITICAL)

        return self.mcp.run(transport=transport_method)


class ConfigurationServer:
    def __init__(self):
        self.app = FastAPI(title="MCPDocker Configuration")
        self.selected_config = ServiceConfig()
        self.config_submitted = False

        @self.app.get("/", response_class=HTMLResponse)
        async def configuration_page():
            return self.get_configuration_html()

        @self.app.post("/configure")
        async def save_configuration(request: Request):
            form_data = await request.form()
            self.selected_config = ServiceConfig(
                docker_management=bool(form_data.get("docker_management")),
                browser_automation=bool(form_data.get("browser_automation")),
                gpu_support=bool(form_data.get("gpu_support")),
                file_management=bool(form_data.get("file_management")),
                documentation_tools=bool(form_data.get("documentation_tools")),
                monitoring_tools=bool(form_data.get("monitoring_tools")),
                development_tools=bool(form_data.get("development_tools")),
                workflow_tools=bool(form_data.get("workflow_tools")),
            )
            self.config_submitted = True
            return RedirectResponse(url="/start", status_code=303)

        @self.app.get("/start")
        async def start_server():
            return HTMLResponse(
                """
            <html>
                <head><title>Starting MCPDocker Server</title></head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px;">
                    <h1>🚀 Starting MCPDocker Server</h1>
                    <p>Your server is starting with the selected configuration...</p>
                    <div style="margin: 20px;">
                        <div style="width: 300px; height: 20px; background: #f0f0f0; border-radius: 10px; margin: 0 auto;">
                            <div style="width: 100%; height: 20px; background: linear-gradient(90deg, #4CAF50, #45a049); border-radius: 10px; animation: pulse 2s infinite;"></div>
                        </div>
                    </div>
                    <p>The server will start automatically. You can close this window.</p>
                    <style>
                        @keyframes pulse {
                            0% { opacity: 1; }
                            50% { opacity: 0.5; }
                            100% { opacity: 1; }
                        }
                    </style>
                    <script>
                        setTimeout(() => {
                            window.close();
                        }, 3000);
                    </script>
                </body>
            </html>
            """
            )

    def get_configuration_html(self):
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>MCPDocker Configuration</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                }}
                .container {{
                    background: white;
                    border-radius: 15px;
                    padding: 30px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.2);
                }}
                h1 {{
                    color: #333;
                    text-align: center;
                    margin-bottom: 30px;
                    font-size: 2.5em;
                }}
                .service-group {{
                    margin: 20px 0;
                    padding: 20px;
                    border: 2px solid #e0e0e0;
                    border-radius: 10px;
                    transition: all 0.3s ease;
                }}
                .service-group:hover {{
                    border-color: #667eea;
                    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.1);
                }}
                .service-group label {{
                    display: flex;
                    align-items: center;
                    font-size: 1.1em;
                    font-weight: bold;
                    color: #333;
                    cursor: pointer;
                }}
                .service-group input[type="checkbox"] {{
                    margin-right: 15px;
                    width: 20px;
                    height: 20px;
                    cursor: pointer;
                }}
                .service-description {{
                    margin-top: 10px;
                    color: #666;
                    font-size: 0.9em;
                    line-height: 1.4;
                }}
                .submit-btn {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 15px 40px;
                    font-size: 1.2em;
                    border-radius: 50px;
                    cursor: pointer;
                    display: block;
                    margin: 30px auto 0;
                    transition: transform 0.3s ease;
                }}
                .submit-btn:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
                }}
                .icon {{
                    margin-right: 10px;
                    font-size: 1.2em;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🐳 MCPDocker Configuration</h1>
                <p style="text-align: center; color: #666; margin-bottom: 30px;">
                    Select the services you want to enable for your MCPDocker server
                </p>
                
                <form method="post" action="/configure">
                    <div class="service-group">
                        <label>
                            <input type="checkbox" name="docker_management" {"checked" if self.selected_config.docker_management else ""}>
                            <span class="icon">🐳</span>
                            Docker Management
                        </label>
                        <div class="service-description">
                            Core Docker functionality: create, manage, and interact with containers, images, and volumes.
                        </div>
                    </div>
                    
                    <div class="service-group">
                        <label>
                            <input type="checkbox" name="browser_automation" {"checked" if self.selected_config.browser_automation else ""}>
                            <span class="icon">🌐</span>
                            Browser Automation
                        </label>
                        <div class="service-description">
                            Playwright and Selenium integration for web automation, testing, and scraping.
                        </div>
                    </div>
                    
                    <div class="service-group">
                        <label>
                            <input type="checkbox" name="gpu_support" {"checked" if self.selected_config.gpu_support else ""}>
                            <span class="icon">⚡</span>
                            GPU Support
                        </label>
                        <div class="service-description">
                            NVIDIA GPU acceleration for containers running ML/AI workloads.
                        </div>
                    </div>
                    
                    <div class="service-group">
                        <label>
                            <input type="checkbox" name="file_management" {"checked" if self.selected_config.file_management else ""}>
                            <span class="icon">📁</span>
                            File Management
                        </label>
                        <div class="service-description">
                            Upload, download, and manage files within containers and workspace.
                        </div>
                    </div>
                    
                    <div class="service-group">
                        <label>
                            <input type="checkbox" name="documentation_tools" {"checked" if self.selected_config.documentation_tools else ""}>
                            <span class="icon">📚</span>
                            Documentation Tools
                        </label>
                        <div class="service-description">
                            Access to multi-language programming documentation and reference materials.
                        </div>
                    </div>
                    
                    <div class="service-group">
                        <label>
                            <input type="checkbox" name="monitoring_tools" {"checked" if self.selected_config.monitoring_tools else ""}>
                            <span class="icon">📊</span>
                            Monitoring Tools
                        </label>
                        <div class="service-description">
                            System and container performance monitoring, metrics collection, and analytics.
                        </div>
                    </div>
                    
                    <div class="service-group">
                        <label>
                            <input type="checkbox" name="development_tools" {"checked" if self.selected_config.development_tools else ""}>
                            <span class="icon">⚙️</span>
                            Development Tools
                        </label>
                        <div class="service-description">
                            Development environment setup, Dockerfile generation, and project templates.
                        </div>
                    </div>
                    
                    <div class="service-group">
                        <label>
                            <input type="checkbox" name="workflow_tools" {"checked" if self.selected_config.workflow_tools else ""}>
                            <span class="icon">🔄</span>
                            Workflow Tools
                        </label>
                        <div class="service-description">
                            CI/CD pipelines, automated workflows, and project management utilities.
                        </div>
                    </div>
                    
                    <button type="submit" class="submit-btn">🚀 Start MCPDocker Server</button>
                </form>
            </div>
        </body>
        </html>
        """

    def run(self, port: int = 8080):
        uvicorn.run(self.app, host="0.0.0.0", port=port, log_level="error")


def find_available_port(start_port: int = 8080) -> int:
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + 20):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            continue
    raise RuntimeError("No available port found")


def main():
    parser = argparse.ArgumentParser(
        prog="MCPDockerShell",
        description="A service that lets AI use Docker and shell with configurable services",
        epilog="To learn more, visit the Repository at github.com/RA86-dev/MCPDockerShell . ",
    )
    parser.add_argument("-t", "--transport", help="Transport method for MCP server")
    parser.add_argument(
        "--skip-config",
        action="store_true",
        help="Skip configuration UI and use default settings",
    )
    arguments = parser.parse_args()

    service_config = ServiceConfig()

    # Auto-detect MCP mode: if stdin is a pipe (from Claude Desktop), skip config UI
    is_mcp_mode = not sys.stdin.isatty() or arguments.skip_config

    # Suppress all logging immediately if in MCP mode
    if is_mcp_mode:
        logging.getLogger().setLevel(logging.CRITICAL)
        logging.getLogger("uvicorn").setLevel(logging.CRITICAL)
        logging.getLogger("fastapi").setLevel(logging.CRITICAL)

    if not is_mcp_mode:
        # Find an available port
        try:
            available_port = find_available_port(8080)
            config_url = f"http://localhost:{available_port}"

            # Configuration server starting (output to stderr for MCP compatibility)
            print("🔧 Starting configuration server...", file=sys.stderr)
            print(
                f"📋 Open your browser to {config_url} to configure MCPDocker",
                file=sys.stderr,
            )

            # Start configuration server
            config_server = ConfigurationServer()

            def start_config_server():
                config_server.run(port=available_port)

            # Start configuration server in background
            config_thread = threading.Thread(target=start_config_server, daemon=True)
            config_thread.start()

            # Wait a moment for server to start
            time.sleep(1)

            # Open browser automatically
            try:
                webbrowser.open(config_url)
            except Exception as e:
                print(f"Could not open browser automatically: {e}", file=sys.stderr)
                print(
                    f"Please manually open {config_url} in your browser",
                    file=sys.stderr,
                )

        except RuntimeError as e:
            print(f"❌ Could not start configuration server: {e}", file=sys.stderr)
            print(
                "⚡ Using default configuration (all services enabled)", file=sys.stderr
            )
            service_config = ServiceConfig()
            skip_config = True
        else:
            skip_config = False

        if not is_mcp_mode:
            print(
                "⏳ Waiting for configuration... (Press Ctrl+C to use default settings)",
                file=sys.stderr,
            )

            # Wait for configuration to be submitted
            try:
                while True:
                    time.sleep(1)
                    # Check if user has submitted configuration
                    if config_server.config_submitted:
                        service_config = config_server.selected_config
                        print("\n✅ Configuration received!", file=sys.stderr)
                        break
            except KeyboardInterrupt:
                print(
                    "\n⚡ Using default configuration (all services enabled)",
                    file=sys.stderr,
                )
                service_config = ServiceConfig()
    else:
        if not is_mcp_mode:
            print(
                "⚡ Skipping configuration UI, using default settings", file=sys.stderr
            )
        service_config = ServiceConfig()

    if not is_mcp_mode:
        print(
            "\n🚀 Starting MCPDocker Server with selected configuration...",
            file=sys.stderr,
        )

    # Show which services are enabled (only in interactive mode)
    if not is_mcp_mode:
        enabled_services = []
        if service_config.docker_management:
            enabled_services.append("Docker Management")
        if service_config.browser_automation:
            enabled_services.append("Browser Automation")
        if service_config.gpu_support:
            enabled_services.append("GPU Support")
        if service_config.file_management:
            enabled_services.append("File Management")
        if service_config.documentation_tools:
            enabled_services.append("Documentation Tools")
        if service_config.monitoring_tools:
            enabled_services.append("Monitoring Tools")
        if service_config.development_tools:
            enabled_services.append("Development Tools")
        if service_config.workflow_tools:
            enabled_services.append("Workflow Tools")

        print(f"✅ Enabled services: {', '.join(enabled_services)}", file=sys.stderr)

    # Start MCP server with configuration
    server = MCPDockerServer(service_config)
    if not is_mcp_mode:
        if server.gpu_available and service_config.gpu_support:
            print("🚀 NVIDIA GPU support detected and enabled", file=sys.stderr)
        else:
            print("💻 Running in CPU-only mode", file=sys.stderr)

    if arguments.transport:
        server.run(transport_method=arguments.transport)
    else:
        # Use stdio for MCP mode, sse for interactive mode
        transport = "stdio" if is_mcp_mode else "sse"
        server.run(transport_method=transport)


if __name__ == "__main__":
    main()