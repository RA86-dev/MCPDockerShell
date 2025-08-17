"""
Name: MCPDevServer
Date: Sunday, August 17th, 2025 14:32


"""
import docker
import os
import tempfile
import argparse
import shutil
import subprocess
import tarfile
import io
import socket
import threading
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
from mcp.server import FastMCP
from mcp.types import Resource, Tool
import json
import time
from pydantic import BaseModel
import uvicorn
import hashlib
import secrets
from functools import wraps
from playwright.async_api import async_playwright, Browser, Page
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import os
import urllib.request
import zipfile


class ContainerConfig(BaseModel):
    image: str
    name: Optional[str] = None
    ports: Dict[int, int] = {}
    volumes: Dict[str, str] = {}
    environment: Dict[str, str] = {}


class MCPDockerServer:
    def __init__(self):
        self.mcp = FastMCP("MCPDocker",host='0.0.0.0')
        self.docker_client = docker.from_env()
        self.active_containers = {}
        self.active_streams = {}
        self.temp_dir = tempfile.mkdtemp(prefix="mcpdocker_")
        
        # Browser automation support
        self.playwright_instance = None
        self.active_browsers = {}
        self.active_selenium_drivers = {}
        
        # Check for NVIDIA GPU support
        self.gpu_available = self._check_nvidia_gpu()
        
        # Multi-language documentation paths
        script_dir = Path(__file__).parent
        self.docs_dir = script_dir / "documentation"
        self.docs_dir.mkdir(exist_ok=True)
        
        # Initialize documentation for multiple languages
        self._ensure_multi_language_docs()
        
        # Comprehensive set of allowed development images
        self.allowed_images = {
            # Base OS images
            "ubuntu:latest", "ubuntu:22.04", "ubuntu:20.04",
            "debian:latest", "debian:bullseye", "debian:bookworm",
            "alpine:latest", "alpine:3.18",
            "fedora:latest", "fedora:38",
            "rockylinux:latest", "rockylinux:9",
            
            # Python development
            "python:latest", "python:3.11", "python:3.10", "python:3.9",
            "python:3.11-slim", "python:3.10-slim",
            
            # Node.js & JavaScript development
            "node:latest", "node:18", "node:16", "node:20",
            "node:18-alpine", "node:16-alpine",
            
            # .NET & C# development
            "mcr.microsoft.com/dotnet/sdk:latest",
            "mcr.microsoft.com/dotnet/sdk:7.0",
            "mcr.microsoft.com/dotnet/sdk:6.0",
            "mcr.microsoft.com/dotnet/runtime:latest",
            "mcr.microsoft.com/dotnet/aspnet:latest",
            
            # Java development
            "openjdk:latest", "openjdk:17", "openjdk:11", "openjdk:8",
            "openjdk:17-alpine", "openjdk:11-alpine",
            "maven:latest", "maven:3.9-openjdk-17",
            "gradle:latest", "gradle:7-jdk17",
            
            # Go development
            "golang:latest", "golang:1.21", "golang:1.20",
            "golang:1.21-alpine", "golang:1.20-alpine",
            
            # Rust development
            "rust:latest", "rust:1.70", "rust:1.69",
            "rust:1.70-alpine", "rust:1.69-alpine",
            
            # PHP development
            "php:latest", "php:8.2", "php:8.1", "php:8.0",
            "php:8.2-fpm", "php:8.1-fpm",
            "composer:latest",
            
            # Ruby development
            "ruby:latest", "ruby:3.2", "ruby:3.1",
            "ruby:3.2-alpine", "ruby:3.1-alpine",
            
            # Database images
            "postgres:latest", "postgres:15", "postgres:14",
            "mysql:latest", "mysql:8", "mysql:5.7",
            "mongo:latest", "mongo:6", "mongo:5",
            "redis:latest", "redis:7", "redis:6",
            "mariadb:latest", "mariadb:10",
            
            # Development tools
            "nginx:latest", "nginx:alpine",
            "httpd:latest", "httpd:alpine",
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
            "linuxserver/code-server:latest"
        }
        
        # Add GPU-enabled images if GPU is available
        if self.gpu_available:
            self.allowed_images.update({
                "nvidia/cuda:latest",
                "pytorch/pytorch:latest",
                "tensorflow/tensorflow:latest-gpu",
                "nvcr.io/nvidia/pytorch:latest",
                "nvcr.io/nvidia/tensorflow:latest-tf2-py3"
            })
        
        self._register_tools()
        self._register_resources()
    
    def _ensure_multi_language_docs(self):
        """Ensure documentation for multiple programming languages is available"""
        # Define supported languages and their documentation sources
        self.supported_languages = {
            'python': {
                'version': '3.13',
                'url_template': 'https://docs.python.org/{version}/archives/python-{version}-docs-text.zip',
                'folder': 'python-docs'
            },
            'csharp': {
                'version': 'net-7.0',
                'url_template': 'https://github.com/dotnet/docs/archive/refs/heads/main.zip',
                'folder': 'csharp-docs'
            },
            'javascript': {
                'version': 'latest',
                'url_template': 'https://github.com/mdn/content/archive/refs/heads/main.zip',
                'folder': 'javascript-docs'
            },
            'java': {
                'version': '17',
                'url_template': 'https://docs.oracle.com/en/java/javase/17/docs/api/',
                'folder': 'java-docs'
            },
            'go': {
                'version': 'latest',
                'url_template': 'https://github.com/golang/go/archive/refs/heads/master.zip',
                'folder': 'go-docs'
            },
            'rust': {
                'version': 'latest',
                'url_template': 'https://github.com/rust-lang/rust/archive/refs/heads/master.zip',
                'folder': 'rust-docs'
            }
        }
        
        # Download Python docs by default (most stable)
        self._download_language_docs('python')
        self._download_language_docs('csharp')
        self._download_language_docs('javascript')
        self._download_language_docs('java')
        self._download_language_docs('go')
        self._download_language_docs('rust')
        
        print("Multi-language documentation system initialized")
    
    def _download_language_docs(self, language: str):
        """Download and extract documentation for various programming languages"""
        if language not in self.supported_languages:
            print(f"Language {language} not supported")
            return
        
        lang_config = self.supported_languages[language]
        lang_docs_dir = self.docs_dir / lang_config['folder']
        
        # Skip download if documentation already exists
        if lang_docs_dir.exists() and any(lang_docs_dir.iterdir()):
            print(f"{language} documentation already exists, skipping download")
            return
            
        lang_docs_dir.mkdir(exist_ok=True)
        
        try:
            if language == 'python':
                self._download_python_docs(lang_config['version'], lang_docs_dir)
            elif language == 'csharp':
                self._download_github_docs(lang_config['url_template'], lang_docs_dir, language)
            elif language == 'javascript':
                self._download_github_docs(lang_config['url_template'], lang_docs_dir, language)
            elif language == 'go':
                self._download_github_docs(lang_config['url_template'], lang_docs_dir, language)
            elif language == 'rust':
                self._download_github_docs(lang_config['url_template'], lang_docs_dir, language)
            elif language == 'java':
                print(f"Java documentation download not implemented yet (complex HTML structure)")
                return
            
            print(f"✅ {language} documentation downloaded successfully")
        except Exception as e:
            print(f"❌ Failed to download {language} documentation: {str(e)}")
    
    def _download_python_docs(self, version: str, target_dir: Path):
        """Download and extract Python documentation"""
        # Download URL for Python documentation
        url = f"https://docs.python.org/{version}/archives/python-{version}-docs-text.zip"
        
        # Download to temporary file
        temp_zip = self.temp_dir + "/python-docs.zip"
        
        print(f"Downloading Python docs from: {url}")
        urllib.request.urlretrieve(url, temp_zip)
        
        # Extract to target directory
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            # Extract all files, but strip the top-level directory
            for member in zip_ref.infolist():
                # Skip the top-level directory
                if '/' in member.filename:
                    # Remove the first directory component
                    member.filename = '/'.join(member.filename.split('/')[1:])
                    if member.filename:  # Don't extract empty filenames
                        zip_ref.extract(member, target_dir)
        
        # Write version info
        version_file = target_dir / "version.txt"
        version_file.write_text(version)
        
        # Clean up temp file
        os.remove(temp_zip)
    
    def _download_github_docs(self, url: str, target_dir: Path, language: str):
        """Download and extract documentation from GitHub repositories"""
        temp_zip = self.temp_dir + f"/{language}-docs.zip"
        
        print(f"Downloading {language} docs from: {url}")
        urllib.request.urlretrieve(url, temp_zip)
        
        # Extract relevant documentation files
        with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
            for member in zip_ref.infolist():
                # Only extract documentation files (markdown, text, etc.)
                if any(member.filename.lower().endswith(ext) for ext in ['.md', '.txt', '.rst']):
                    # Skip large directories and focus on docs
                    if any(doc_dir in member.filename.lower() for doc_dir in ['doc', 'guide', 'tutorial', 'readme']):
                        try:
                            # Clean up the path structure
                            clean_path = '/'.join(member.filename.split('/')[1:])  # Remove root directory
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
            result = subprocess.run(["nvidia-smi"], capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return False
            
            # Check if Docker has GPU runtime support
            try:
                info = self.docker_client.info()
                runtimes = info.get('Runtimes', {})
                return 'nvidia' in runtimes or any('nvidia' in runtime for runtime in runtimes.keys())
            except:
                return False
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
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
                timeout=30
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
    
    def _register_tools(self):

        @self.mcp.tool()
        async def list_allowed_images() -> List[str]:
            """List allowed Docker images that can be used to create containers"""
            return sorted(list(self.allowed_images))
        @self.mcp.tool()
        async def get_gpu_status() -> str:
            """Get NVIDIA GPU status and availability"""
            if not self.gpu_available:
                return "GPU Status: Not available or not configured"
            
            try:
                # Get GPU info using nvidia-smi
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    gpu_info = []
                    for i, line in enumerate(lines):
                        parts = line.split(', ')
                        if len(parts) >= 4:
                            name, total_mem, used_mem, util = parts[:4]
                            gpu_info.append(f"GPU {i}: {name} | Memory: {used_mem}MB/{total_mem}MB | Utilization: {util}%")
                    
                    return f"GPU Status: Available\n" + "\n".join(gpu_info)
                else:
                    return f"GPU Status: Available but nvidia-smi error: {result.stderr}"
                    
            except Exception as e:
                return f"GPU Status: Available but error getting details: {str(e)}"
        
        @self.mcp.tool()
        async def create_container(
            image: str,
            name: str = None,
            ports: Dict[int, int] = None,
            environment: Dict[str, str] = None,
            command: str = None,
            use_gpu: bool = False
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
                volumes = {
                    self.temp_dir: {'bind': '/workspace', 'mode': 'rw'}
                }
                
                # Default command to keep container running
                default_command = command or "tail -f /dev/null"
                
                # GPU configuration
                device_requests = []
                if use_gpu and self.gpu_available:
                    device_requests = [docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]
                
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
                    device_requests=device_requests
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
                
                with open(file_path, 'w', encoding='utf-8') as f:
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
                        rel_path = os.path.relpath(os.path.join(root, filename), self.temp_dir)
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
                
                logs = container.logs(tail=tail).decode('utf-8')
                
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
            
            return self._run_docker_scout_command(["compare", "--to", target_image, base_image])
        
        @self.mcp.tool()
        async def scout_policy_evaluation(image: str, policy: str = "default") -> str:
            """Evaluate a Docker image against security policies using Docker Scout"""
            if image not in self.allowed_images:
                return f"Image '{image}' not allowed. Use list_allowed_images to see available options."
            
            return self._run_docker_scout_command(["policy", image, "--policy", policy])
        
        @self.mcp.tool()
        async def copy_file_to_container(container_id: str, local_path: str, container_path: str) -> str:
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
                with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                    tar.add(source_path, arcname=os.path.basename(container_path))
                tar_stream.seek(0)
                
                # Extract to the container
                container_dir = os.path.dirname(container_path) or '/'
                container.put_archive(container_dir, tar_stream.getvalue())
                
                return f"File copied from {local_path} to {container_path} in container {container_id[:12]}"
                
            except Exception as e:
                return f"Error copying file to container: {str(e)}"
        
        @self.mcp.tool()
        async def copy_file_from_container(container_id: str, container_path: str, local_path: str = None) -> str:
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
                tar_data = b''.join(chunk for chunk in tar_stream)
                with tarfile.open(fileobj=io.BytesIO(tar_data)) as tar:
                    # Extract the first file in the archive
                    members = tar.getmembers()
                    if members:
                        file_data = tar.extractfile(members[0])
                        if file_data:
                            with open(dest_path, 'wb') as f:
                                f.write(file_data.read())
                
                return f"File copied from {container_path} in container {container_id[:12]} to {local_path}"
                
            except Exception as e:
                return f"Error copying file from container: {str(e)}"
        
        @self.mcp.tool()
        async def create_file_in_container(container_id: str, file_path: str, content: str) -> str:
            """Create a file with specified content inside a container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"
                
                # Create a temporary file in workspace first
                temp_file = Path(self.temp_dir) / f"temp_{os.path.basename(file_path)}"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Copy to container
                tar_stream = io.BytesIO()
                with tarfile.open(fileobj=tar_stream, mode='w') as tar:
                    tar.add(temp_file, arcname=os.path.basename(file_path))
                tar_stream.seek(0)
                
                container_dir = os.path.dirname(file_path) or '/'
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
                    return f"File {file_path} deleted from container {container_id[:12]}"
                else:
                    return f"Error deleting file: {result.output.decode('utf-8')}"
                
            except Exception as e:
                return f"Error deleting file in container: {str(e)}"
        
        @self.mcp.tool()
        async def list_files_in_container(container_id: str, directory_path: str = "/workspace") -> str:
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
        async def create_directory_in_container(container_id: str, directory_path: str) -> str:
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
        async def move_file_in_container(container_id: str, source_path: str, dest_path: str) -> str:
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
        async def copy_file_in_container(container_id: str, source_path: str, dest_path: str) -> str:
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
                    return result.output.decode('utf-8')
                else:
                    return f"Error reading file: {result.output.decode('utf-8')}"
                
            except Exception as e:
                return f"Error reading file in container: {str(e)}"
        
        @self.mcp.tool()
        async def write_file_in_container(container_id: str, file_path: str, content: str, append: bool = False) -> str:
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
                    return f"Content {action} {file_path} in container {container_id[:12]}"
                else:
                    return f"Error writing file: {result.output.decode('utf-8')}"
                
            except Exception as e:
                return f"Error writing file in container: {str(e)}"
        
        @self.mcp.tool()
        async def start_port_stream(container_id: str, container_port: int, host_port: int = None) -> str:
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
                    daemon=True
                )
                stream_thread.start()
                
                self.active_streams[stream_key] = {
                    'container_id': container_id,
                    'container_port': container_port,
                    'host_port': host_port,
                    'thread': stream_thread
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
                container_id = stream_info['container_id'][:12]
                container_port = stream_info['container_port']
                host_port = stream_info['host_port']
                streams.append(f"{container_id}:{container_port} -> localhost:{host_port}")
            
            return streams
        
        @self.mcp.tool()
        async def stream_container_logs(container_id: str, follow: bool = True, tail: int = 100) -> str:
            """Stream container logs in real-time with JSON responses"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return json.dumps({"error": f"Container {container_id} not found"})
                
                if not follow:
                    # Return static logs
                    logs = container.logs(tail=tail).decode('utf-8')
                    return json.dumps({
                        "type": "logs", 
                        "container_id": container_id[:12],
                        "data": logs,
                        "streaming": False
                    })
                
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
                                "data": log_line.decode('utf-8').strip(),
                                "stream_key": stream_key
                            }
                            
                            # Store in stream buffer for retrieval
                            if stream_key not in self.active_streams:
                                self.active_streams[stream_key] = {"buffer": [], "type": "logs"}
                            
                            self.active_streams[stream_key]["buffer"].append(log_data)
                            
                            # Keep buffer size manageable
                            if len(self.active_streams[stream_key]["buffer"]) > 1000:
                                self.active_streams[stream_key]["buffer"] = self.active_streams[stream_key]["buffer"][-500:]
                            
                    except Exception as e:
                        error_data = {
                            "type": "error",
                            "container_id": container_id[:12],
                            "timestamp": time.time(),
                            "error": str(e),
                            "stream_key": stream_key
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
                    "thread": stream_thread
                }
                
                return json.dumps({
                    "type": "stream_started",
                    "container_id": container_id[:12],
                    "stream_key": stream_key,
                    "message": f"Started streaming logs for container {container_id[:12]}",
                    "streaming": True
                })
                
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
                
                return json.dumps({
                    "type": "stream_data",
                    "stream_key": stream_key,
                    "last_index": len(buffer),
                    "data": new_data,
                    "has_more": len(new_data) > 0
                })
                
            except Exception as e:
                return json.dumps({"error": f"Error getting stream data: {str(e)}"})
        
        @self.mcp.tool()
        async def stop_stream(stream_key: str) -> str:
            """Stop an active MCP stream"""
            try:
                if stream_key not in self.active_streams:
                    return json.dumps({"error": f"Stream {stream_key} not found"})
                
                stream_info = self.active_streams.pop(stream_key)
                
                return json.dumps({
                    "type": "stream_stopped",
                    "stream_key": stream_key,
                    "message": f"Stream {stream_key} stopped successfully"
                })
                
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
                            exec_instance['Id'], stream=True
                        )
                        
                        for chunk in exec_stream:
                            if stream_key not in self.active_streams:
                                break
                                
                            output_data = {
                                "type": "command_output",
                                "container_id": container_id[:12],
                                "command": command,
                                "timestamp": time.time(),
                                "data": chunk.decode('utf-8'),
                                "stream_key": stream_key
                            }
                            
                            if stream_key not in self.active_streams:
                                self.active_streams[stream_key] = {"buffer": [], "type": "command"}
                            
                            self.active_streams[stream_key]["buffer"].append(output_data)
                            
                            # Keep buffer manageable
                            if len(self.active_streams[stream_key]["buffer"]) > 1000:
                                self.active_streams[stream_key]["buffer"] = self.active_streams[stream_key]["buffer"][-500:]
                        
                        # Get exit code
                        exec_info = container.client.api.exec_inspect(exec_instance['Id'])
                        exit_code = exec_info.get('ExitCode', 0)
                        
                        completion_data = {
                            "type": "command_completed",
                            "container_id": container_id[:12],
                            "command": command,
                            "timestamp": time.time(),
                            "exit_code": exit_code,
                            "stream_key": stream_key
                        }
                        
                        if stream_key in self.active_streams:
                            self.active_streams[stream_key]["buffer"].append(completion_data)
                            
                    except Exception as e:
                        error_data = {
                            "type": "command_error",
                            "container_id": container_id[:12],
                            "command": command,
                            "timestamp": time.time(),
                            "error": str(e),
                            "stream_key": stream_key
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
                    "thread": exec_thread
                }
                
                return json.dumps({
                    "type": "stream_started",
                    "container_id": container_id[:12],
                    "command": command,
                    "stream_key": stream_key,
                    "message": f"Started streaming command execution in container {container_id[:12]}",
                    "streaming": True
                })
                
            except Exception as e:
                return json.dumps({"error": f"Error streaming command execution: {str(e)}"})
        
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
                        "container_id": stream_info.get("container_id", "")[:12] if stream_info.get("container_id") else ""
                    }
                    
                    if stream_info.get("command"):
                        stream_detail["command"] = stream_info["command"]
                    
                    streams.append(stream_detail)
                
                return json.dumps({
                    "streams": streams,
                    "count": len(streams)
                })
                
            except Exception as e:
                return json.dumps({"error": f"Error listing streams: {str(e)}"})
        
        # Playwright Tools
        @self.mcp.tool()
        async def playwright_launch_browser(browser_type: str = "chromium", headless: bool = True, args: List[str] = None) -> str:
            """Launch a Playwright browser instance (chromium, firefox, or webkit)"""
            try:
                if self.playwright_instance is None:
                    self.playwright_instance = await async_playwright().start()
                
                browser_args = args or []
                
                if browser_type.lower() == "chromium":
                    browser = await self.playwright_instance.chromium.launch(
                        headless=headless,
                        args=browser_args
                    )
                elif browser_type.lower() == "firefox":
                    browser = await self.playwright_instance.firefox.launch(
                        headless=headless,
                        args=browser_args
                    )
                elif browser_type.lower() == "webkit":
                    browser = await self.playwright_instance.webkit.launch(
                        headless=headless,
                        args=browser_args
                    )
                else:
                    return f"Unsupported browser type: {browser_type}. Use chromium, firefox, or webkit."
                
                browser_id = f"pw_{browser_type}_{len(self.active_browsers)}"
                self.active_browsers[browser_id] = browser
                
                return f"Browser {browser_type} launched with ID: {browser_id}"
                
            except Exception as e:
                return f"Error launching browser: {str(e)}"
        
        @self.mcp.tool()
        async def playwright_create_page(browser_id: str, viewport_width: int = 1920, viewport_height: int = 1080) -> str:
            """Create a new page in a Playwright browser"""
            try:
                if browser_id not in self.active_browsers:
                    return f"Browser {browser_id} not found"
                
                browser = self.active_browsers[browser_id]
                page = await browser.new_page(viewport={'width': viewport_width, 'height': viewport_height})
                
                # Store page reference in browser for tracking
                if not hasattr(browser, '_page_references'):
                    browser._page_references = {}
                
                page_id = f"{browser_id}_page_{len(browser._page_references)}"
                browser._page_references[page_id] = page
                
                return f"Page created with ID: {page_id}"
                
            except Exception as e:
                return f"Error creating page: {str(e)}"
        
        @self.mcp.tool()
        async def playwright_navigate(page_id: str, url: str, wait_until: str = "load") -> str:
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
        async def playwright_click(page_id: str, selector: str, timeout: int = 30000) -> str:
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
        async def playwright_type(page_id: str, selector: str, text: str, timeout: int = 30000) -> str:
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
        async def playwright_screenshot(page_id: str, filename: str = None, full_page: bool = False, return_base64: bool = False) -> str:
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
                    with open(screenshot_path, 'wb') as f:
                        f.write(screenshot_bytes)
                    
                    import base64
                    screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                    
                    return json.dumps({
                        "type": "screenshot",
                        "filename": filename,
                        "path": str(screenshot_path),
                        "base64": screenshot_base64,
                        "format": "png",
                        "message": f"Screenshot saved to {filename} and available for AI viewing"
                    })
                else:
                    # Regular file-only screenshot
                    await page.screenshot(path=str(screenshot_path), full_page=full_page)
                    return f"Screenshot saved to {filename}"
                
            except Exception as e:
                return f"Error taking screenshot: {str(e)}"
        
        @self.mcp.tool()
        async def playwright_get_text(page_id: str, selector: str, timeout: int = 30000) -> str:
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
        async def playwright_wait_for_selector(page_id: str, selector: str, timeout: int = 30000, state: str = "visible") -> str:
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
                    if hasattr(browser, '_page_references') and page_id in browser._page_references:
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
        async def selenium_launch_driver(browser_type: str = "chrome", headless: bool = True, options: List[str] = None) -> str:
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
        async def selenium_click(driver_id: str, selector: str, by: str = "css", timeout: int = 10) -> str:
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
                    "tag": By.TAG_NAME
                }
                
                if by not in by_mapping:
                    return f"Invalid selector type: {by}. Use css, xpath, id, name, class, or tag."
                
                element = wait.until(EC.element_to_be_clickable((by_mapping[by], selector)))
                element.click()
                
                return f"Clicked element: {selector}"
                
            except Exception as e:
                return f"Error clicking element: {str(e)}"
        
        @self.mcp.tool()
        async def selenium_type(driver_id: str, selector: str, text: str, by: str = "css", timeout: int = 10, clear: bool = True) -> str:
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
                    "tag": By.TAG_NAME
                }
                
                if by not in by_mapping:
                    return f"Invalid selector type: {by}. Use css, xpath, id, name, class, or tag."
                
                element = wait.until(EC.presence_of_element_located((by_mapping[by], selector)))
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
        async def selenium_get_text(driver_id: str, selector: str, by: str = "css", timeout: int = 10) -> str:
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
                    "tag": By.TAG_NAME
                }
                
                if by not in by_mapping:
                    return f"Invalid selector type: {by}. Use css, xpath, id, name, class, or tag."
                
                element = wait.until(EC.presence_of_element_located((by_mapping[by], selector)))
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
                
                return str(result) if result is not None else "Script executed successfully"
                
            except Exception as e:
                return f"Error executing script: {str(e)}"
        
        @self.mcp.tool()
        async def selenium_wait_for_element(driver_id: str, selector: str, by: str = "css", timeout: int = 10, condition: str = "presence") -> str:
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
                    "tag": By.TAG_NAME
                }
                
                if by not in by_mapping:
                    return f"Invalid selector type: {by}. Use css, xpath, id, name, class, or tag."
                
                condition_mapping = {
                    "presence": EC.presence_of_element_located,
                    "visible": EC.visibility_of_element_located,
                    "clickable": EC.element_to_be_clickable
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
                
                if not file_path.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                    return f"File {filename} is not a valid image format"
                
                import base64
                with open(file_path, 'rb') as f:
                    image_bytes = f.read()
                
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                
                return json.dumps({
                    "type": "image_share",
                    "filename": filename,
                    "path": str(file_path),
                    "base64": image_base64,
                    "format": file_path.suffix.lower().replace('.', ''),
                    "message": f"Screenshot {filename} is now available for AI viewing"
                })
                
            except Exception as e:
                return f"Error sharing screenshot: {str(e)}"
        
        @self.mcp.tool()
        async def list_python_docs() -> List[str]:
            """List available Python documentation files"""
            try:
                python_docs_dir = self.docs_dir / "python-docs"
                if not python_docs_dir.exists():
                    return ["Python documentation not available. Try downloading first."]
                
                docs_files = []
                for root, _, files in os.walk(python_docs_dir):
                    for file in files:
                        if file.endswith(('.txt', '.md', '.rst')):
                            rel_path = os.path.relpath(os.path.join(root, file), python_docs_dir)
                            docs_files.append(rel_path)
                
                return sorted(docs_files) if docs_files else ["No documentation files found"]
                
            except Exception as e:
                return [f"Error listing Python docs: {str(e)}"]
        
        @self.mcp.tool()
        async def read_python_doc(file_path: str, max_lines: int = 500) -> str:
            """Read a specific Python documentation file"""
            try:
                python_docs_dir = self.docs_dir / "python-docs"
                doc_file = python_docs_dir / file_path
                
                if not doc_file.exists():
                    return f"Documentation file {file_path} not found"
                
                if not doc_file.suffix in ['.txt', '.md', '.rst']:
                    return f"File {file_path} is not a supported documentation file format"
                
                with open(doc_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if len(lines) > max_lines:
                    content = ''.join(lines[:max_lines])
                    content += f"\n\n[Content truncated - showing first {max_lines} lines of {len(lines)} total lines]"
                else:
                    content = ''.join(lines)
                
                return content
                
            except Exception as e:
                return f"Error reading Python documentation: {str(e)}"
        
        @self.mcp.tool()
        async def search_python_docs(query: str, max_results: int = 10) -> str:
            """Search through Python documentation for specific content"""
            try:
                python_docs_dir = self.docs_dir / "python-docs"
                if not python_docs_dir.exists():
                    return "Python documentation not available. Try downloading first."
                
                query_lower = query.lower()
                results = []
                
                for root, _, files in os.walk(python_docs_dir):
                    for file in files:
                        if not file.endswith(('.txt', '.md', '.rst')):
                            continue
                            
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, python_docs_dir)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Search for query in content (case insensitive)
                            if query_lower in content.lower():
                                # Find context around matches
                                lines = content.split('\n')
                                matches = []
                                
                                for i, line in enumerate(lines):
                                    if query_lower in line.lower():
                                        # Get context lines
                                        start = max(0, i - 2)
                                        end = min(len(lines), i + 3)
                                        context = '\n'.join(lines[start:end])
                                        matches.append(f"Line {i+1}: {context}")
                                        
                                        if len(matches) >= 3:  # Limit matches per file
                                            break
                                
                                if matches:
                                    results.append({
                                        'file': rel_path,
                                        'matches': matches[:3]  # Limit to 3 matches per file
                                    })
                                    
                                    if len(results) >= max_results:
                                        break
                        except:
                            continue
                
                if not results:
                    return f"No matches found for '{query}' in Python documentation"
                
                # Format results
                output = f"Found {len(results)} files containing '{query}':\n\n"
                for result in results:
                    output += f"📄 {result['file']}:\n"
                    for match in result['matches']:
                        output += f"   {match}\n\n"
                    output += "-" * 50 + "\n\n"
                
                return output
                
            except Exception as e:
                return f"Error searching Python documentation: {str(e)}"
        
        @self.mcp.tool()
        async def get_python_doc_info() -> str:
            """Get information about the downloaded Python documentation"""
            try:
                version_file = self.docs_dir / "version.txt"
                
                if not self.docs_dir.exists():
                    return "Python documentation not downloaded yet"
                
                version = "Unknown"
                if version_file.exists():
                    try:
                        version = version_file.read_text().strip()
                    except:
                        pass
                
                # Count files
                doc_count = 0
                total_size = 0
                for root, _, files in os.walk(self.docs_dir):
                    for file in files:
                        if file.endswith('.txt'):
                            doc_count += 1
                            file_path = os.path.join(root, file)
                            try:
                                total_size += os.path.getsize(file_path)
                            except:
                                pass
                
                size_mb = total_size / (1024 * 1024)
                
                return f"""Python Documentation Info:
📖 Version: Python {version}
📁 Location: {self.docs_dir}
📄 Files: {doc_count} documentation files
💾 Size: {size_mb:.1f} MB
🔍 Status: Ready for AI reading and searching"""
                
            except Exception as e:
                return f"Error getting Python documentation info: {str(e)}"
        
        @self.mcp.tool()
        async def list_language_docs(language: str) -> List[str]:
            """List available documentation files for a specific programming language (python, csharp, javascript, java, go, rust)"""
            try:
                if language not in self.supported_languages:
                    return [f"Language '{language}' not supported. Available: {', '.join(self.supported_languages.keys())}"]
                
                lang_config = self.supported_languages[language]
                lang_docs_dir = self.docs_dir / lang_config['folder']
                
                if not lang_docs_dir.exists():
                    return [f"{language} documentation not available. Try downloading first."]
                
                docs_files = []
                for root, _, files in os.walk(lang_docs_dir):
                    for file in files:
                        if file.endswith(('.txt', '.md', '.rst')):
                            rel_path = os.path.relpath(os.path.join(root, file), lang_docs_dir)
                            docs_files.append(rel_path)
                
                return sorted(docs_files) if docs_files else ["No documentation files found"]
                
            except Exception as e:
                return [f"Error listing {language} docs: {str(e)}"]
        
        @self.mcp.tool()
        async def read_language_doc(language: str, file_path: str, max_lines: int = 500) -> str:
            """Read a specific documentation file for a programming language (python, csharp, javascript, java, go, rust)"""
            try:
                if language not in self.supported_languages:
                    return f"Language '{language}' not supported. Available: {', '.join(self.supported_languages.keys())}"
                
                lang_config = self.supported_languages[language]
                lang_docs_dir = self.docs_dir / lang_config['folder']
                doc_file = lang_docs_dir / file_path
                
                if not doc_file.exists():
                    return f"Documentation file {file_path} not found for {language}"
                
                if not doc_file.suffix in ['.txt', '.md', '.rst']:
                    return f"File {file_path} is not a supported documentation file format"
                
                with open(doc_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                if len(lines) > max_lines:
                    content = ''.join(lines[:max_lines])
                    content += f"\n\n[Content truncated - showing first {max_lines} lines of {len(lines)} total lines]"
                else:
                    content = ''.join(lines)
                
                return content
                
            except Exception as e:
                return f"Error reading {language} documentation: {str(e)}"
        
        @self.mcp.tool()
        async def search_language_docs(language: str, query: str, max_results: int = 10) -> str:
            """Search through documentation for a specific programming language (python, csharp, javascript, java, go, rust)"""
            try:
                if language not in self.supported_languages:
                    return f"Language '{language}' not supported. Available: {', '.join(self.supported_languages.keys())}"
                
                lang_config = self.supported_languages[language]
                lang_docs_dir = self.docs_dir / lang_config['folder']
                
                if not lang_docs_dir.exists():
                    return f"{language} documentation not available. Try downloading first."
                
                query_lower = query.lower()
                results = []
                
                for root, _, files in os.walk(lang_docs_dir):
                    for file in files:
                        if not file.endswith(('.txt', '.md', '.rst')):
                            continue
                            
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, lang_docs_dir)
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Search for query in content (case insensitive)
                            if query_lower in content.lower():
                                # Find context around matches
                                lines = content.split('\n')
                                matches = []
                                
                                for i, line in enumerate(lines):
                                    if query_lower in line.lower():
                                        # Get context lines
                                        start = max(0, i - 2)
                                        end = min(len(lines), i + 3)
                                        context = '\n'.join(lines[start:end])
                                        matches.append(f"Line {i+1}: {context}")
                                        
                                        if len(matches) >= 3:  # Limit matches per file
                                            break
                                
                                if matches:
                                    results.append({
                                        'file': rel_path,
                                        'matches': matches[:3]  # Limit to 3 matches per file
                                    })
                                    
                                    if len(results) >= max_results:
                                        break
                        except:
                            continue
                
                if not results:
                    return f"No matches found for '{query}' in {language} documentation"
                
                # Format results
                output = f"Found {len(results)} files containing '{query}' in {language} documentation:\n\n"
                for result in results:
                    output += f"📄 {result['file']}:\n"
                    for match in result['matches']:
                        output += f"   {match}\n\n"
                    output += "-" * 50 + "\n\n"
                
                return output
                
            except Exception as e:
                return f"Error searching {language} documentation: {str(e)}"
        
        @self.mcp.tool()
        async def get_language_doc_info(language: str) -> str:
            """Get information about downloaded documentation for a specific programming language (python, csharp, javascript, java, go, rust)"""
            try:
                if language not in self.supported_languages:
                    return f"Language '{language}' not supported. Available: {', '.join(self.supported_languages.keys())}"
                
                lang_config = self.supported_languages[language]
                lang_docs_dir = self.docs_dir / lang_config['folder']
                version_file = lang_docs_dir / "version.txt"
                
                if not lang_docs_dir.exists():
                    return f"{language} documentation not downloaded yet"
                
                version = lang_config.get('version', 'Unknown')
                if version_file.exists():
                    try:
                        version = version_file.read_text().strip()
                    except:
                        pass
                
                # Count files
                doc_count = 0
                total_size = 0
                for root, _, files in os.walk(lang_docs_dir):
                    for file in files:
                        if file.endswith(('.txt', '.md', '.rst')):
                            doc_count += 1
                            file_path = os.path.join(root, file)
                            try:
                                total_size += os.path.getsize(file_path)
                            except:
                                pass
                
                size_mb = total_size / (1024 * 1024)
                
                return f"""{language.title()} Documentation Info:
📖 Version: {version}
📁 Location: {lang_docs_dir}
📄 Files: {doc_count} documentation files
💾 Size: {size_mb:.1f} MB
🔍 Status: Ready for AI reading and searching"""
                
            except Exception as e:
                return f"Error getting {language} documentation info: {str(e)}"
        
        @self.mcp.tool()
        async def download_language_docs(language: str) -> str:
            """Download documentation for a specific programming language (python, csharp, javascript, java, go, rust)"""
            try:
                if language not in self.supported_languages:
                    return f"Language '{language}' not supported. Available: {', '.join(self.supported_languages.keys())}"
                
                print(f"Starting download for {language} documentation...")
                self._download_language_docs(language)
                return f"✅ {language} documentation download completed successfully"
                
            except Exception as e:
                return f"❌ Error downloading {language} documentation: {str(e)}"
        
        @self.mcp.tool()
        async def list_supported_languages() -> List[str]:
            """List all supported programming languages for documentation"""
            try:
                languages_info = []
                for lang, config in self.supported_languages.items():
                    lang_docs_dir = self.docs_dir / config['folder']
                    status = "✅ Available" if lang_docs_dir.exists() and any(lang_docs_dir.iterdir()) else "❌ Not downloaded"
                    languages_info.append(f"{lang.title()} ({config['version']}) - {status}")
                
                return languages_info
                
            except Exception as e:
                return [f"Error listing supported languages: {str(e)}"]
    
    def _register_resources(self):
        """Register MCP resources for documentation access"""
        
        @self.mcp.resource("documentation://languages")
        async def list_documentation_languages() -> str:
            """List all supported programming languages for documentation"""
            try:
                languages_info = []
                for lang, config in self.supported_languages.items():
                    lang_docs_dir = self.docs_dir / config['folder']
                    if lang_docs_dir.exists() and any(lang_docs_dir.iterdir()):
                        languages_info.append({
                            'language': lang,
                            'version': config.get('version', 'Unknown'),
                            'folder': config['folder'],
                            'available': True
                        })
                    else:
                        languages_info.append({
                            'language': lang,
                            'version': config.get('version', 'Unknown'),
                            'folder': config['folder'],
                            'available': False
                        })
                
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
                lang_docs_dir = self.docs_dir / lang_config['folder']
                
                if not lang_docs_dir.exists():
                    return json.dumps({"error": f"{language} documentation not available"})
                
                files_info = []
                for root, _, files in os.walk(lang_docs_dir):
                    for file in files:
                        if file.endswith(('.txt', '.md', '.rst')):
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, lang_docs_dir)
                            try:
                                file_size = os.path.getsize(file_path)
                                files_info.append({
                                    'path': rel_path,
                                    'size': file_size,
                                    'type': file.split('.')[-1]
                                })
                            except:
                                continue
                
                return json.dumps({
                    'language': language,
                    'files': sorted(files_info, key=lambda x: x['path'])
                }, indent=2)
                
            except Exception as e:
                return json.dumps({"error": f"Error listing files: {str(e)}"})
        
        @self.mcp.resource("documentation://{language}/file/{file_path}")
        async def get_documentation_file(language: str, file_path: str) -> str:
            """Get content of a specific documentation file"""
            try:
                if language not in self.supported_languages:
                    return json.dumps({"error": f"Language '{language}' not supported"})
                
                lang_config = self.supported_languages[language]
                lang_docs_dir = self.docs_dir / lang_config['folder']
                doc_file = lang_docs_dir / file_path
                
                if not doc_file.exists():
                    return json.dumps({"error": f"File {file_path} not found"})
                
                if not doc_file.suffix in ['.txt', '.md', '.rst']:
                    return json.dumps({"error": f"File format not supported"})
                
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return json.dumps({
                    'language': language,
                    'file_path': file_path,
                    'content': content,
                    'size': len(content),
                    'type': doc_file.suffix[1:]
                }, indent=2)
                
            except Exception as e:
                return json.dumps({"error": f"Error reading file: {str(e)}"})
    
    async def _get_playwright_page(self, page_id: str):
        """Helper method to get a Playwright page by ID"""
        for browser in self.active_browsers.values():
            if hasattr(browser, '_page_references') and page_id in browser._page_references:
                return browser._page_references[page_id]
        return f"Page {page_id} not found"
    
    def _start_stream_server(self, container, container_port: int, host_port: int, stream_key: str):
        """Start a TCP server that streams data from container port to host port"""
        try:
            # Create server socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind(('localhost', host_port))
            server_socket.listen(5)
            server_socket.settimeout(1.0)  # Non-blocking accept with timeout
            
            print(f"Stream server listening on localhost:{host_port} for container port {container_port}")
            
            while stream_key in self.active_streams:
                try:
                    client_socket, addr = server_socket.accept()
                    print(f"Client connected from {addr} to stream {stream_key}")
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_stream_client,
                        args=(client_socket, container, container_port, stream_key),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"Error accepting connection for stream {stream_key}: {e}")
                    break
            
            server_socket.close()
            print(f"Stream server stopped for {stream_key}")
            
        except Exception as e:
            print(f"Error in stream server for {stream_key}: {e}")
    
    def _handle_stream_client(self, client_socket, container, container_port: int, stream_key: str):
        """Handle individual client connection for streaming"""
        try:
            # Connect to container port
            container_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            container_socket.settimeout(5.0)
            
            # Get container IP
            container.reload()
            container_ip = container.attrs['NetworkSettings']['IPAddress']
            
            if not container_ip:
                # Try getting IP from networks
                networks = container.attrs['NetworkSettings']['Networks']
                if networks:
                    container_ip = list(networks.values())[0]['IPAddress']
            
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
                target=forward_data,
                args=(client_socket, container_socket),
                daemon=True
            )
            container_to_client = threading.Thread(
                target=forward_data,
                args=(container_socket, client_socket),
                daemon=True
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
            print(f"Error in stream client handler for {stream_key}: {e}")
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
        
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def run(self,transport_method: str="stdio"):
        """Run the MCP server"""
        return self.mcp.run(transport=transport_method)


def main():
    parser = argparse.ArgumentParser(
        prog='MCPDockerShell',
        description="A service that lets AI use Docker and shell",
        epilog="To learn more, visit the Repository at github.com/RA86-dev/MCPDockerShell . "   
    )
    parser.add_argument("-t","--transport")
    arguments = parser.parse_args()

    
    print("🌐 FastAPI web interface starting at http://localhost:8080")
    print("🐳 MCP Docker server starting...")
    
    # Start MCP server (this will block)
    server = MCPDockerServer()
    if server.gpu_available:
        print("🚀 NVIDIA GPU support detected and enabled")
    else:
        print("💻 Running in CPU-only mode")
    if arguments.transport:
        server.run(transport_method=arguments.transport)
    else:
        server.run(transport_method="stdio")
if __name__ == "__main__":
    main()
