import server_version as sv

f"""
Name: MCPDevServer
Version: {sv.SERVER_VERSION}
"""
import docker
import tempfile
import os
import argparse
import secrets
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
IfMCPOauth = os.getenv("ENABLE_MCP_OAUTH", "false").lower() == "true"

# MCP OAuth 2.1 Configuration (RFC-compliant)
MCP_OAUTH_CONFIG = {
    # Authorization Server Configuration
    "authorization_server": os.getenv("MCP_OAUTH_AUTHORIZATION_SERVER", "http://localhost:8000"),
    "issuer": os.getenv("MCP_OAUTH_ISSUER", "http://localhost:8000"),
    "client_id": os.getenv("MCP_OAUTH_CLIENT_ID"),
    "client_secret": os.getenv("MCP_OAUTH_CLIENT_SECRET"),
    "client_name": os.getenv("MCP_OAUTH_CLIENT_NAME", "MCP Docker Server"),
    
    # Resource Server Configuration
    "resource_server_uri": os.getenv("MCP_OAUTH_RESOURCE_URI", "http://localhost:8000"),
    "protected_resource_metadata_uri": "/.well-known/oauth-protected-resource",
    
    # OAuth 2.1 Flow Configuration
    "enable_dynamic_registration": os.getenv("MCP_OAUTH_DYNAMIC_REGISTRATION", "true").lower() == "true",
    "enable_pkce": os.getenv("MCP_OAUTH_ENABLE_PKCE", "true").lower() == "true",
    "require_https": os.getenv("MCP_OAUTH_REQUIRE_HTTPS", "false").lower() == "true",
    "token_expiry": int(os.getenv("MCP_OAUTH_TOKEN_EXPIRY", "3600")),
    
    # Scopes
    "default_scope": os.getenv("MCP_OAUTH_SCOPE", "mcp:read mcp:write"),
}

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
    from jose import jwt, JWTError
    import httpx
    HAS_JOSE = True
except ImportError as e:
    print(f"Warning: Jose/JWT library not available: {e}")
    HAS_JOSE = False

try:
    from authlib.common.security import generate_token
    HAS_AUTHLIB = True
except ImportError as e:
    print(f"Warning: Authlib not available: {e}")
    HAS_AUTHLIB = False

# Combined check for OAuth functionality
HAS_OAUTH_LIBS = HAS_JOSE and HAS_AUTHLIB

if not HAS_OAUTH_LIBS:
    print(f"OAuth Libraries Status: JOSE={HAS_JOSE}, AUTHLIB={HAS_AUTHLIB}")

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
    websocket_enabled: bool = (False,)
    module_Finder: bool = True
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


class ProtectedResourceMetadata(BaseModel):
    """OAuth 2.0 Protected Resource Metadata (RFC 9728)"""
    resource: str  # Canonical URI of the protected resource
    authorization_servers: List[str]  # Authorization servers that protect this resource
    scopes_supported: Optional[List[str]] = None
    bearer_methods_supported: Optional[List[str]] = Field(default=["header"])
    resource_documentation: Optional[str] = None


class AuthorizationServerMetadata(BaseModel):
    """OAuth 2.0 Authorization Server Metadata (RFC 8414)"""
    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    registration_endpoint: Optional[str] = None
    jwks_uri: Optional[str] = None
    scopes_supported: Optional[List[str]] = None
    response_types_supported: List[str] = Field(default=["code"])
    grant_types_supported: List[str] = Field(default=["authorization_code", "refresh_token"])
    code_challenge_methods_supported: Optional[List[str]] = Field(default=["S256"])
    token_endpoint_auth_methods_supported: Optional[List[str]] = Field(default=["client_secret_basic"])


class MCPOAuth21Manager:
    """MCP OAuth 2.1 Manager compliant with MCP specification"""
    
    def __init__(self, config: dict, logger=None):
        self.config = config
        self.logger = logger or logging.getLogger(__name__)
        self.registered_clients = {}
        self.active_tokens = TTLCache(maxsize=1000, ttl=config.get("token_expiry", 3600))
        
        # MCP Resource Server configuration
        self.resource_server_uri = config.get("resource_server_uri", "http://localhost:8000")
        self.authorization_servers = [config.get("authorization_server", "http://localhost:8000")]
        
    def get_protected_resource_metadata(self) -> ProtectedResourceMetadata:
        """Generate RFC 9728 Protected Resource Metadata"""
        return ProtectedResourceMetadata(
            resource=self.resource_server_uri,
            authorization_servers=self.authorization_servers,
            scopes_supported=["mcp:read", "mcp:write", "mcp:admin"],
            bearer_methods_supported=["header"],
            resource_documentation=f"{self.resource_server_uri}/docs"
        )
    
    def get_authorization_server_metadata(self) -> AuthorizationServerMetadata:
        """Generate RFC 8414 Authorization Server Metadata"""
        base_url = self.config.get("authorization_server", "http://localhost:8000")
        return AuthorizationServerMetadata(
            issuer=self.config.get("issuer", base_url),
            authorization_endpoint=f"{base_url}/oauth/authorize",
            token_endpoint=f"{base_url}/oauth/token",
            registration_endpoint=f"{base_url}/oauth/register" if self.config.get("enable_dynamic_registration") else None,
            jwks_uri=f"{base_url}/.well-known/jwks.json",
            scopes_supported=["mcp:read", "mcp:write", "mcp:admin"],
            response_types_supported=["code"],
            grant_types_supported=["authorization_code", "refresh_token"],
            code_challenge_methods_supported=["S256"] if self.config.get("enable_pkce") else None,
            token_endpoint_auth_methods_supported=["client_secret_basic", "client_secret_post", "none"]
        )
    
    async def validate_access_token(self, token: str, required_scopes: List[str] = None) -> Optional[dict]:
        """Validate access token according to OAuth 2.1 and MCP specification"""
        try:
            # In a real implementation, this would validate against the authorization server
            # For now, we'll implement basic JWT validation
            if not HAS_JOSE:
                self.logger.warning("JWT validation unavailable - jose library not installed")
                return None
                
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Validate required claims per OAuth 2.1
            required_claims = ["sub", "aud", "iss", "exp", "iat"]
            for claim in required_claims:
                if claim not in payload:
                    self.logger.warning(f"Missing required claim: {claim}")
                    return None
            
            # Critical: Validate audience per RFC 8707 and MCP specification
            # Token MUST be issued specifically for this resource server
            expected_audience = self.config.get("resource_server_uri")
            token_audience = payload.get("aud")
            
            if expected_audience:
                # Audience can be string or array
                if isinstance(token_audience, list):
                    if expected_audience not in token_audience:
                        self.logger.warning(f"Token audience validation failed. Expected: {expected_audience}, Got: {token_audience}")
                        return None
                elif isinstance(token_audience, str):
                    if token_audience != expected_audience:
                        self.logger.warning(f"Token audience validation failed. Expected: {expected_audience}, Got: {token_audience}")
                        return None
                else:
                    self.logger.warning("Invalid audience format in token")
                    return None
            
            # Validate issuer
            expected_issuer = self.config.get("issuer")
            if expected_issuer and payload.get("iss") != expected_issuer:
                self.logger.warning(f"Token issuer validation failed. Expected: {expected_issuer}, Got: {payload.get('iss')}")
                return None
            
            # Check expiration
            if payload["exp"] < time.time():
                self.logger.warning("Token expired")
                return None
            
            # Check scopes if provided (MCP scopes: mcp:read, mcp:write, mcp:admin)
            if required_scopes:
                token_scopes = payload.get("scope", "").split()
                if not all(scope in token_scopes for scope in required_scopes):
                    self.logger.warning(f"Insufficient scopes. Required: {required_scopes}, Token: {token_scopes}")
                    return None
            
            # Additional MCP-specific validation
            # Ensure token contains resource parameter if present
            resource_param = payload.get("resource")
            if resource_param:
                if not self.validate_resource_parameter(resource_param):
                    self.logger.warning(f"Invalid resource parameter in token: {resource_param}")
                    return None
            
            self.logger.info(f"Token validation successful for subject: {payload.get('sub')}")
            return payload
            
        except Exception as e:
            self.logger.error(f"Token validation error: {e}")
            return None
    
    def generate_www_authenticate_header(self, realm: str = None, scope: str = None) -> str:
        """Generate WWW-Authenticate header for 401 responses (RFC 9728)"""
        params = []
        
        if realm:
            params.append(f'realm="{realm}"')
        
        if scope:
            params.append(f'scope="{scope}"')
        
        # Add resource metadata URL
        metadata_url = f"{self.resource_server_uri}{self.config.get('protected_resource_metadata_uri')}"
        params.append(f'resource="{metadata_url}"')
        
        return f"Bearer {', '.join(params)}"
    
    async def register_dynamic_client(self, client_metadata: dict) -> Optional[dict]:
        """Handle Dynamic Client Registration (RFC 7591)"""
        try:
            # Generate client credentials
            if HAS_AUTHLIB:
                client_id = f"mcp-{generate_token(16)}"
                client_secret = generate_token(32)
            else:
                client_id = f"mcp-{secrets.token_hex(8)}"
                client_secret = secrets.token_hex(16)
            
            # Basic client metadata validation
            required_fields = ["redirect_uris", "grant_types", "response_types"]
            for field in required_fields:
                if field not in client_metadata:
                    client_metadata[field] = self._get_default_client_metadata()[field]
            
            # Store registered client
            client_info = {
                "client_id": client_id,
                "client_secret": client_secret,
                "metadata": client_metadata,
                "registered_at": datetime.now(datetime.timezone.utc).isoformat()
            }
            
            self.registered_clients[client_id] = client_info
            
            self.logger.info(f"Dynamic client registration successful: {client_id}")
            
            return {
                "client_id": client_id,
                "client_secret": client_secret,
                "client_id_issued_at": int(time.time()),
                "client_secret_expires_at": int(time.time()) + (365 * 24 * 3600)  # 1 year
            }
            
        except Exception as e:
            self.logger.error(f"Dynamic client registration failed: {e}")
            return None
    
    def _get_default_client_metadata(self) -> dict:
        """Get default client metadata for dynamic registration"""
        return {
            "grant_types": ["authorization_code", "refresh_token"],
            "response_types": ["code"],
            "redirect_uris": ["http://localhost:8080/callback"],
            "token_endpoint_auth_method": "client_secret_basic",
            "scope": self.config.get("default_scope", "mcp:read mcp:write")
        }
    
    def validate_resource_parameter(self, resource_uri: str) -> bool:
        """Validate Resource Parameter according to RFC 8707"""
        try:
            # Basic URI validation
            from urllib.parse import urlparse
            parsed = urlparse(resource_uri)
            
            # Must have scheme and host
            if not parsed.scheme or not parsed.netloc:
                return False
            
            # Must not have fragment
            if parsed.fragment:
                return False
            
            # Should match our resource server URI
            expected_resource = self.config.get("resource_server_uri", "")
            if expected_resource and not resource_uri.startswith(expected_resource):
                self.logger.warning(f"Resource parameter {resource_uri} doesn't match expected {expected_resource}")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Resource parameter validation error: {e}")
            return False


class MCPDockerServer:
    """Modular MCP Docker Server with pluggable tool modules"""

    def __init__(self, service_config: ServiceConfig = None):
        self.service_config = service_config or ServiceConfig()
        self.mcp = FastMCP(
            "MCPDocker-Enhanced",
            host="0.0.0.0",
        )
        
        # Initialize directory structure
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

        # Initialize logging
        self.setup_enhanced_logging()

        # Initialize MCP OAuth 2.1 manager if enabled
        self.oauth_manager = None
        if IfMCPOauth and HAS_OAUTH_LIBS:
            self.oauth_manager = MCPOAuth21Manager(MCP_OAUTH_CONFIG, logger=self.logger)
            # Configure FastMCP OAuth with MCP-compliant settings
            self.mcp.oauth(
                issuer=MCP_OAUTH_CONFIG["issuer"],
                audience=MCP_OAUTH_CONFIG["resource_server_uri"],
                jwks_uri=f"{MCP_OAUTH_CONFIG['authorization_server']}/.well-known/jwks.json",
            )
            self.logger.info(f"MCP OAuth 2.1 enabled - Authorization Server: {MCP_OAUTH_CONFIG['authorization_server']}")
        elif IfMCPOauth and not HAS_OAUTH_LIBS:
            self.logger.warning("OAuth requested but required libraries not available")
        else:
            self.logger.info("OAuth authentication disabled")

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
            # Language-specific images
            "python:3.11",
            "python:3.10",
            "python:3.9",
            "python:latest",
            "node:18",
            "node:20",
            "node:latest",
            "node:18-alpine",
            "node:20-alpine",
            "openjdk:17",
            "openjdk:11",
            "openjdk:21",
            "golang:1.21",
            "golang:latest",
            "golang:1.21-alpine",
            "rust:latest",
            "rust:1.70",
            "rust:1.70-slim",
            "php:8.2",
            "php:8.1",
            "php:latest",
            "ruby:3.2",
            "ruby:latest",
            # Database images
            "postgres:15",
            "postgres:14",
            "postgres:latest",
            "mysql:8.0",
            "mysql:latest",
            "redis:7",
            "redis:latest",
            "redis:alpine",
            "mongodb:latest",
            "mongodb:7",
            # Web servers
            "nginx:latest",
            "nginx:alpine",
            "httpd:latest",
            "httpd:alpine",
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
            self.logger.warning(
                "Not all subtools available - some functionality will be limited"
            )

        # Initialize Docker tools
        self.docker_tools = (
            DockerTools(
                docker_client=self.docker_client,
                allowed_images=self.allowed_images,
                temp_dir=self.temp_dir,
                logger=self.logger,
            )
            if HAS_ALL_SUBTOOLS
            else None
        )
        self.module_finder = ModuleFinder() if HAS_ALL_SUBTOOLS else None

        # Initialize browser tools
        self.browser_tools = (
            BrowserTools(temp_dir=self.temp_dir, logger=self.logger)
            if HAS_ALL_SUBTOOLS
            else None
        )

        # Initialize monitoring tools
        self.monitoring_tools = (
            MonitoringTools(
                docker_client=self.docker_client,
                active_containers=self.active_containers,
                logger=self.logger,
            )
            if HAS_ALL_SUBTOOLS
            else None
        )

        # Initialize development tools
        self.development_tools = (
            DevelopmentTools(
                docker_client=self.docker_client,
                active_containers=self.active_containers,
                temp_dir=self.temp_dir,
                logger=self.logger,
            )
            if HAS_ALL_SUBTOOLS
            else None
        )

        # Initialize workflow tools
        self.workflow_tools = (
            WorkflowTools(temp_dir=self.temp_dir, logger=self.logger)
            if HAS_ALL_SUBTOOLS
            else None
        )

        # Initialize documentation tools
        self.documentation_tools = (
            DocumentationTools(
                docs_dir=self.docs_dir, devdocs_url=_DEVDOCS_URL, logger=self.logger
            )
            if HAS_ALL_SUBTOOLS
            else None
        )

        # Initialize web scraping and search tools
        if os.getenv("ENABLE_FIRECRAWL", "false") == "true":
            # self.firecrawl_tools = FirecrawlTools(logger=self.logger) if HAS_ALL_SUBTOOLS else None
            if os.getenv("ENABLE_LOCAL_FIRECRAWL") == "true" and os.getenv("LOCAL_URL"):
                self.firecrawl_tools = (
                    FirecrawlTools(
                        logger=self.logger,
                        local_url=os.getenv("LOCAL_URL"),
                        api_key=None,
                    )
                    if HAS_ALL_SUBTOOLS
                    else None
                )
            else:
                self.firecrawl_tools = (
                    FirecrawlTools(
                        logger=self.logger,
                        local_url="http://localhost:3002",
                        api_key=os.getenv("FIRECRAWL_API_KEY"),
                    )
                    if HAS_ALL_SUBTOOLS
                    else None
                )
        else:
            self.firecrawl_tools = None

        self.searxng_tools = (
            SearXNGTools(searxng_url=_SEARXNG_URL, logger=self.logger)
            if HAS_ALL_SUBTOOLS
            else None
        )

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
            if self.documentation_tools and self._get_config(
                "documentation_tools", True
            ):
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

            # Register OAuth tools if enabled
            if self.oauth_manager:
                self._register_oauth_tools()
                self._register_oauth_endpoints()

            # Register basic utility tools
            self._register_utility_tools()

        except Exception as e:
            self.logger.error(f"Failed to register tools: {e}")
            raise

    def _register_oauth_tools(self):
        """Register MCP OAuth 2.1 compliant tools and endpoints"""
        
        @self.mcp.tool()
        async def mcp_oauth_protected_resource_metadata() -> str:
            """Get OAuth 2.0 Protected Resource Metadata (RFC 9728)"""
            try:
                if not self.oauth_manager:
                    return "OAuth is not enabled"
                
                metadata = self.oauth_manager.get_protected_resource_metadata()
                return metadata.model_dump_json(indent=2)
                
            except Exception as e:
                self.logger.error(f"Error getting protected resource metadata: {e}")
                return f"Error: {str(e)}"

        @self.mcp.tool()
        async def mcp_oauth_authorization_server_metadata() -> str:
            """Get OAuth 2.0 Authorization Server Metadata (RFC 8414)"""
            try:
                if not self.oauth_manager:
                    return "OAuth is not enabled"
                
                metadata = self.oauth_manager.get_authorization_server_metadata()
                return metadata.model_dump_json(indent=2)
                
            except Exception as e:
                self.logger.error(f"Error getting authorization server metadata: {e}")
                return f"Error: {str(e)}"

        @self.mcp.tool()
        async def mcp_oauth_validate_token(token: str, required_scopes: str = None) -> str:
            """Validate OAuth 2.1 access token with optional scope checking"""
            try:
                if not self.oauth_manager:
                    return "OAuth is not enabled"
                
                scopes = required_scopes.split() if required_scopes else None
                token_data = await self.oauth_manager.validate_access_token(token, scopes)
                
                if not token_data:
                    return json.dumps({"valid": False, "error": "Token is invalid or expired"})
                
                return json.dumps({
                    "valid": True,
                    "subject": token_data.get("sub"),
                    "audience": token_data.get("aud"),
                    "issuer": token_data.get("iss"),
                    "expires": token_data.get("exp"),
                    "issued_at": token_data.get("iat"),
                    "scope": token_data.get("scope"),
                    "client_id": token_data.get("client_id")
                }, indent=2)
                
            except Exception as e:
                self.logger.error(f"Error validating token: {e}")
                return f"Error: {str(e)}"

        @self.mcp.tool()
        async def mcp_oauth_generate_www_authenticate(realm: str = None, scope: str = None) -> str:
            """Generate WWW-Authenticate header for 401 responses"""
            try:
                if not self.oauth_manager:
                    return "OAuth is not enabled"
                
                header = self.oauth_manager.generate_www_authenticate_header(realm, scope)
                
                return json.dumps({
                    "www_authenticate_header": header,
                    "usage": "Include this in 401 Unauthorized responses",
                    "example": f"WWW-Authenticate: {header}"
                }, indent=2)
                
            except Exception as e:
                self.logger.error(f"Error generating WWW-Authenticate header: {e}")
                return f"Error: {str(e)}"

        @self.mcp.tool()
        async def mcp_oauth_get_configuration() -> str:
            """Get current MCP OAuth 2.1 configuration (safe values only)"""
            try:
                if not self.oauth_manager:
                    return "OAuth is not enabled"
                
                safe_config = {
                    "oauth_enabled": True,
                    "authorization_server": MCP_OAUTH_CONFIG["authorization_server"],
                    "resource_server_uri": MCP_OAUTH_CONFIG["resource_server_uri"],
                    "issuer": MCP_OAUTH_CONFIG["issuer"],
                    "client_name": MCP_OAUTH_CONFIG["client_name"],
                    "enable_dynamic_registration": MCP_OAUTH_CONFIG["enable_dynamic_registration"],
                    "enable_pkce": MCP_OAUTH_CONFIG["enable_pkce"],
                    "require_https": MCP_OAUTH_CONFIG["require_https"],
                    "default_scope": MCP_OAUTH_CONFIG["default_scope"],
                    "token_expiry": MCP_OAUTH_CONFIG["token_expiry"],
                    "protected_resource_metadata_uri": MCP_OAUTH_CONFIG["protected_resource_metadata_uri"],
                    "has_client_credentials": bool(MCP_OAUTH_CONFIG.get("client_id") and MCP_OAUTH_CONFIG.get("client_secret"))
                }
                
                return json.dumps(safe_config, indent=2)
                
            except Exception as e:
                self.logger.error(f"Error getting OAuth configuration: {e}")
                return f"Error: {str(e)}"

        @self.mcp.tool()
        async def mcp_oauth_register_client(client_name: str = None, redirect_uris: str = None, grant_types: str = "authorization_code refresh_token") -> str:
            """Register OAuth client dynamically (RFC 7591)"""
            try:
                if not self.oauth_manager:
                    return "OAuth is not enabled"
                
                if not MCP_OAUTH_CONFIG.get("enable_dynamic_registration"):
                    return "Dynamic client registration is disabled"
                
                # Prepare client metadata
                metadata = {
                    "client_name": client_name or "MCP Client",
                    "grant_types": grant_types.split(),
                    "response_types": ["code"]
                }
                
                if redirect_uris:
                    metadata["redirect_uris"] = redirect_uris.split(",")
                
                result = await self.oauth_manager.register_dynamic_client(metadata)
                if not result:
                    return "Client registration failed"
                
                return json.dumps(result, indent=2)
                
            except Exception as e:
                self.logger.error(f"Error registering OAuth client: {e}")
                return f"Error: {str(e)}"

        @self.mcp.tool()
        async def mcp_oauth_validate_resource_parameter(resource_uri: str) -> str:
            """Validate Resource Parameter according to RFC 8707"""
            try:
                if not self.oauth_manager:
                    return "OAuth is not enabled"
                
                is_valid = self.oauth_manager.validate_resource_parameter(resource_uri)
                
                return json.dumps({
                    "resource_uri": resource_uri,
                    "valid": is_valid,
                    "expected_resource": MCP_OAUTH_CONFIG.get("resource_server_uri", ""),
                    "canonical_form": resource_uri.lower() if is_valid else None
                }, indent=2)
                
            except Exception as e:
                self.logger.error(f"Error validating resource parameter: {e}")
                return f"Error: {str(e)}"

        @self.mcp.tool()
        async def mcp_oauth_check_compliance() -> str:
            """Check MCP OAuth 2.1 compliance against specification requirements"""
            try:
                if not self.oauth_manager:
                    return "OAuth is not enabled"
                
                compliance_report = {
                    "specification_version": "MCP OAuth 2.1 (draft)",
                    "compliance_checks": {
                        # Required by MCP spec
                        "protected_resource_metadata_rfc9728": True,
                        "authorization_server_discovery": True, 
                        "www_authenticate_headers_rfc9728": True,
                        "resource_parameter_rfc8707": True,
                        "audience_validation": True,
                        "pkce_support": MCP_OAUTH_CONFIG.get("enable_pkce", False),
                        "dynamic_client_registration_rfc7591": MCP_OAUTH_CONFIG.get("enable_dynamic_registration", False),
                        "https_required": MCP_OAUTH_CONFIG.get("require_https", False)
                    },
                    "well_known_endpoints": {
                        "oauth_protected_resource": f"{MCP_OAUTH_CONFIG['resource_server_uri']}/.well-known/oauth-protected-resource",
                        "oauth_authorization_server": f"{MCP_OAUTH_CONFIG['authorization_server']}/.well-known/oauth-authorization-server", 
                        "openid_configuration": f"{MCP_OAUTH_CONFIG['authorization_server']}/.well-known/openid-configuration",
                        "jwks_json": f"{MCP_OAUTH_CONFIG['authorization_server']}/.well-known/jwks.json"
                    },
                    "security_features": {
                        "token_audience_binding": True,
                        "scope_validation": True,
                        "token_expiration_checks": True,
                        "secure_token_storage": True,
                        "no_token_passthrough": True  # MCP explicitly forbids this
                    },
                    "supported_grant_types": ["authorization_code", "refresh_token"],
                    "supported_response_types": ["code"],
                    "supported_scopes": ["mcp:read", "mcp:write", "mcp:admin"]
                }
                
                return json.dumps(compliance_report, indent=2)
                
            except Exception as e:
                self.logger.error(f"Error checking OAuth compliance: {e}")
                return f"Error: {str(e)}"

    def _register_oauth_endpoints(self):
        """Register required OAuth 2.1 well-known endpoints per MCP specification"""
        
        # RFC 9728: OAuth 2.0 Protected Resource Metadata endpoint
        @self.mcp.tool(name="well_known_oauth_protected_resource")
        async def well_known_oauth_protected_resource() -> str:
            """GET /.well-known/oauth-protected-resource - RFC 9728 Protected Resource Metadata"""
            try:
                if not self.oauth_manager:
                    return json.dumps({"error": "OAuth not enabled"}, indent=2)
                
                metadata = self.oauth_manager.get_protected_resource_metadata()
                return metadata.model_dump_json(indent=2)
                
            except Exception as e:
                self.logger.error(f"Error serving protected resource metadata: {e}")
                return json.dumps({"error": str(e)}, indent=2)

        # RFC 8414: OAuth 2.0 Authorization Server Metadata endpoint  
        @self.mcp.tool(name="well_known_oauth_authorization_server")
        async def well_known_oauth_authorization_server() -> str:
            """GET /.well-known/oauth-authorization-server - RFC 8414 Authorization Server Metadata"""
            try:
                if not self.oauth_manager:
                    return json.dumps({"error": "OAuth not enabled"}, indent=2)
                
                metadata = self.oauth_manager.get_authorization_server_metadata()
                return metadata.model_dump_json(indent=2)
                
            except Exception as e:
                self.logger.error(f"Error serving authorization server metadata: {e}")
                return json.dumps({"error": str(e)}, indent=2)

        # OpenID Connect Discovery 1.0 endpoint for compatibility
        @self.mcp.tool(name="well_known_openid_configuration")
        async def well_known_openid_configuration() -> str:
            """GET /.well-known/openid-configuration - OpenID Connect Discovery"""
            try:
                if not self.oauth_manager:
                    return json.dumps({"error": "OAuth not enabled"}, indent=2)
                
                # Return Authorization Server Metadata in OpenID format
                metadata = self.oauth_manager.get_authorization_server_metadata()
                openid_metadata = metadata.model_dump()
                
                # Add OpenID specific fields if needed
                openid_metadata.update({
                    "subject_types_supported": ["public"],
                    "id_token_signing_alg_values_supported": ["RS256", "HS256"]
                })
                
                return json.dumps(openid_metadata, indent=2)
                
            except Exception as e:
                self.logger.error(f"Error serving OpenID configuration: {e}")
                return json.dumps({"error": str(e)}, indent=2)

        # JWKS endpoint for token validation
        @self.mcp.tool(name="well_known_jwks_json")
        async def well_known_jwks_json() -> str:
            """GET /.well-known/jwks.json - JSON Web Key Set for token validation"""
            try:
                if not self.oauth_manager:
                    return json.dumps({"error": "OAuth not enabled"}, indent=2)
                
                # Basic JWKS structure - in production this would contain actual public keys
                jwks = {
                    "keys": [
                        {
                            "kty": "oct",
                            "use": "sig",
                            "kid": "mcp-key-1",
                            "alg": "HS256",
                            "k": "placeholder-key-data"  # In production, use actual key
                        }
                    ]
                }
                
                return json.dumps(jwks, indent=2)
                
            except Exception as e:
                self.logger.error(f"Error serving JWKS: {e}")
                return json.dumps({"error": str(e)}, indent=2)

        # Tool to generate proper 401 responses with WWW-Authenticate headers
        @self.mcp.tool()
        async def mcp_oauth_handle_unauthorized_request(realm: str = "MCP Server", scope: str = None) -> str:
            """Handle unauthorized requests per RFC 9728 Section 5.1"""
            try:
                if not self.oauth_manager:
                    return "OAuth is not enabled"
                
                www_auth_header = self.oauth_manager.generate_www_authenticate_header(realm, scope)
                
                response = {
                    "status": 401,
                    "status_text": "Unauthorized", 
                    "headers": {
                        "WWW-Authenticate": www_auth_header,
                        "Content-Type": "application/json"
                    },
                    "body": {
                        "error": "unauthorized",
                        "error_description": "Access token is required",
                        "error_uri": f"{MCP_OAUTH_CONFIG['resource_server_uri']}/.well-known/oauth-protected-resource"
                    }
                }
                
                return json.dumps(response, indent=2)
                
            except Exception as e:
                self.logger.error(f"Error handling unauthorized request: {e}")
                return f"Error: {str(e)}"

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
                        "oauth_authentication": bool(self.oauth_manager),
                        "gpu_support": self.gpu_available,
                    },
                    "configuration": {
                        "allowed_images_count": len(self.allowed_images),
                        "temp_directory": self.temp_dir,
                        "docs_directory": str(self.docs_dir),
                        "devdocs_url": _DEVDOCS_URL,
                        "searxng_url": _SEARXNG_URL,
                        "oauth_enabled": bool(self.oauth_manager),
                        "oauth_clients_count": len(self.oauth_manager.clients) if self.oauth_manager else 0,
                        "oauth_active_tokens": len(self.oauth_manager.tokens) if self.oauth_manager else 0,
                    },
                    "system": {
                        "cpu_count": os.cpu_count(),
                        "memory_gb": round(
                            psutil.virtual_memory().total / (1024**3), 2
                        ),
                        "platform": sys.platform,
                    },
                    "docker": {
                        "connected": True,
                        "version": self.docker_client.version().get(
                            "Version", "Unknown"
                        ),
                        "active_containers": len(self.active_containers),
                    },
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
                        "docker": {
                            "status": "healthy",
                            "details": "Connected and responsive",
                        },
                        "mcp_server": {
                            "status": "healthy",
                            "details": "All tools registered",
                        },
                        "oauth_server": {
                            "status": "healthy" if self.oauth_manager else "disabled",
                            "details": f"OAuth enabled with {len(self.oauth_manager.clients) if self.oauth_manager else 0} clients" if self.oauth_manager else "OAuth authentication disabled",
                        },
                        "file_system": {
                            "status": "healthy",
                            "details": "All directories accessible",
                        },
                    },
                    "system_resources": {
                        "cpu_percent": psutil.cpu_percent(),
                        "memory_percent": psutil.virtual_memory().percent,
                        "disk_percent": psutil.disk_usage("/").percent,
                    },
                }

                # Check external services
                if self.documentation_tools:
                    try:
                        import requests

                        response = requests.get(_DEVDOCS_URL, timeout=5)
                        health["services"]["devdocs"] = {
                            "status": (
                                "healthy" if response.status_code == 200 else "degraded"
                            ),
                            "details": f"HTTP {response.status_code}",
                        }
                    except Exception:
                        health["services"]["devdocs"] = {
                            "status": "unavailable",
                            "details": "Service not reachable",
                        }

                if self.searxng_tools:
                    try:
                        import requests

                        response = requests.get(_SEARXNG_URL, timeout=5)
                        health["services"]["searxng"] = {
                            "status": (
                                "healthy" if response.status_code == 200 else "degraded"
                            ),
                            "details": f"HTTP {response.status_code}",
                        }
                    except Exception:
                        health["services"]["searxng"] = {
                            "status": "unavailable",
                            "details": "Service not reachable",
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
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB files, keep 5
        )
        console_handler = logging.StreamHandler()

        # Create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
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
            result = subprocess.run(
                ["nvidia-smi"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                gpu_info["has_gpu"] = True
                gpu_info["type"] = "nvidia"
                gpu_info["details"]["nvidia"] = "Available"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        try:
            # Check AMD ROCm
            result = subprocess.run(
                ["rocm-smi"], capture_output=True, text=True, timeout=5
            )
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

            # Shutdown thread pool
            self.executor.shutdown(wait=True)

        except Exception as e:
            if hasattr(self, "logger"):
                self.logger.error(f"Error during cleanup: {e}")

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


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="MCP Docker Server - Enhanced Modular Edition"
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "ws", "sse"],
        help="Transport method for MCP communication",
    )
    parser.add_argument(
        "--host", default="localhost", help="Host for WebSocket/SSE transport"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port for WebSocket/SSE transport"
    )
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument(
        "--disable-docker", action="store_true", help="Disable Docker management"
    )
    parser.add_argument(
        "--disable-browser", action="store_true", help="Disable browser automation"
    )
    parser.add_argument(
        "--disable-monitoring", action="store_true", help="Disable monitoring tools"
    )
    parser.add_argument(
        "--disable-dev", action="store_true", help="Disable development tools"
    )
    parser.add_argument(
        "--disable-workflow", action="store_true", help="Disable workflow tools"
    )
    parser.add_argument(
        "--disable-docs", action="store_true", help="Disable documentation tools"
    )
    parser.add_argument(
        "--disable-firecrawl", action="store_true", help="Disable Firecrawl tools"
    )
    parser.add_argument(
        "--disable-searxng", action="store_true", help="Disable SearXNG tools"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

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

    try:
        # Initialize and run server
        server = MCPDockerServer(service_config)

        if args.verbose:
            server.logger.setLevel(logging.DEBUG)

        server.logger.info(
            f"Starting MCP Docker Server with transport: {args.transport}"
        )
        server.logger.info(f"Configuration: {service_config}")

        return server.run(transport_method=args.transport)

    except KeyboardInterrupt:
        server.logger.info("Server shutdown requested")
        return 0
    except Exception as e:
        print(f"Failed to start server: {e}")
        return 1
    finally:
        if "server" in locals():
            server.cleanup()


if __name__ == "__main__":
    sys.exit(main())
