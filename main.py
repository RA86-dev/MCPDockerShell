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

class ContainerConfig(BaseModel):
    image: str
    name: Optional[str] = None
    ports: Dict[int, int] = {}
    volumes: Dict[str, str] = {}
    environment: Dict[str, str] = {}


class MCPDockerServer:
    def __init__(self):
        self.mcp = FastMCP("MCPDocker")
        self.docker_client = docker.from_env()
        self.active_containers = {}
        self.active_streams = {}
        self.temp_dir = tempfile.mkdtemp(prefix="mcpdocker_")
        
        # Check for NVIDIA GPU support
        self.gpu_available = self._check_nvidia_gpu()
        
        # Limited set of allowed images for security
        self.allowed_images = {
            "ubuntu:latest",
            "debian:latest", 
            "fedora:latest",
            "python:latest",
            "node:latest",
            "alpine:latest",
            # "centos:latest", (Deprecated)
            "rockylinux:latest"
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
        async def download_file(filename: str) -> str:
            """Download a file from the shared workspace"""
            try:
                file_path = Path(self.temp_dir) / filename
                
                if not file_path.exists():
                    return f"File {filename} not found"
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return content
                
            except Exception as e:
                return f"Error downloading file: {str(e)}"
        
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
        """Clean up containers, streams, and temporary files"""
        # Stop all active streams
        self.active_streams.clear()
        
        # Stop and remove containers
        for container in self.active_containers.values():
            try:
                container.stop()
                container.remove()
            except:
                pass
        
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
    if arguments.transport and arguments.server_ui == False:
        server.run(transport_method=arguments.transport)
    else:
        server.run(transport_method="stdio")
if __name__ == "__main__":
    main()
