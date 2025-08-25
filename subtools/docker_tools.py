"""
Docker management tools for container operations
"""
import docker
import tempfile
import os
import tarfile
import io
import subprocess
import json
import time
import psutil
from typing import List, Dict, Any, Optional
from pathlib import Path


class DockerTools:
    """Core Docker management functionality"""

    def __init__(self, docker_client, allowed_images: set, temp_dir: str, logger=None):
        self.docker_client = docker_client
        self.allowed_images = allowed_images
        self.temp_dir = temp_dir
        self.logger = logger
        self.active_containers = {}
        self.active_streams = {}

    def register_tools(self, mcp_server):
        """Register Docker management tools with the MCP server"""

        @mcp_server.tool()
        async def list_allowed_images() -> List[str]:
            """List allowed Docker images that can be used to create containers"""
            return sorted(list(self.allowed_images))
        @mcp_server.tool()
        async def inspect_container(container: str):
            """Inspects the container, and runs the command docker command"""
            inspected = subprocess.run(
                ["docker","container","inspect",container],
                capture_output=True,timeout=20
            )
            if inspected.returncode == 0:
                data = inspected.stdout
                return json.dumps(data)
            else:
                return f"Error: {inspected.stderr}"

        @mcp_server.tool()
        async def get_gpu_status() -> str:
            """Get GPU status and availability (NVIDIA and AMD)"""
            status_info = []

            # Check NVIDIA GPU status
            try:
                result = subprocess.run(
                    ["nvidia-smi", "--query-gpu=name,memory.total,memory.used,utilization.gpu", "--format=csv,noheader,nounits"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    nvidia_info = []
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            name, mem_total, mem_used, utilization = [x.strip() for x in line.split(',')]
                            nvidia_info.append({
                                "name": name,
                                "memory_total_mb": int(mem_total),
                                "memory_used_mb": int(mem_used),
                                "utilization_percent": int(utilization)
                            })
                    status_info.append({"type": "NVIDIA", "gpus": nvidia_info, "available": True})
                else:
                    status_info.append({"type": "NVIDIA", "available": False, "error": "nvidia-smi failed"})
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                status_info.append({"type": "NVIDIA", "available": False, "error": "nvidia-smi not found or failed"})

            # Check AMD ROCm status
            try:
                result = subprocess.run(["rocm-smi", "--showproductname", "--showmeminfo", "vram", "--showuse"],
                                       capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    status_info.append({"type": "AMD_ROCm", "available": True, "info": "ROCm detected"})
                else:
                    status_info.append({"type": "AMD_ROCm", "available": False, "error": "rocm-smi failed"})
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                status_info.append({"type": "AMD_ROCm", "available": False, "error": "rocm-smi not found"})

            return json.dumps(status_info, indent=2)

        @mcp_server.tool()
        async def create_container(
            image: str,
            name: str = None,
            command: str = None,
            environment: Dict[str, str] = None,
            ports: Dict[str, int] = None,
            use_gpu: bool = False
        ) -> str:
            """Create and start a new Docker container that runs indefinitely"""
            if image not in self.allowed_images:
                return f"Error: Image '{image}' is not in the allowed list. Use list_allowed_images() to see available images."

            try:
                container_config = {
                    "image": image,
                    "detach": True,
                    "stdin_open": True,
                    "tty": True,
                    "working_dir": "/workspace"
                }

                if name:
                    container_config["name"] = name

                if command:
                    container_config["command"] = command
                else:
                    if "ubuntu" in image.lower() or "debian" in image.lower():
                        container_config["command"] = "/bin/bash"
                    elif "alpine" in image.lower():
                        container_config["command"] = "/bin/sh"
                    elif "python" in image.lower():
                        container_config["command"] = "/bin/bash"
                    elif "node" in image.lower():
                        container_config["command"] = "/bin/sh"
                    else:
                        container_config["command"] = "/bin/sh"

                if environment:
                    container_config["environment"] = environment

                if ports:
                    container_config["ports"] = ports

                # GPU support
                if use_gpu:
                    try:
                        container_config["runtime"] = "nvidia"
                        if not environment:
                            container_config["environment"] = {}
                        container_config["environment"]["NVIDIA_VISIBLE_DEVICES"] = "all"
                    except Exception as gpu_error:
                        if self.logger:
                            self.logger.warning(f"GPU configuration failed: {gpu_error}")

                # Create workspace volume
                container_config["volumes"] = {"/tmp/workspace": {"bind": "/workspace", "mode": "rw"}}
                os.makedirs("/tmp/workspace", exist_ok=True)

                container = self.docker_client.containers.run(**container_config)

                self.active_containers[container.id] = {
                    "container": container,
                    "name": name or container.name,
                    "created_at": time.time(),
                    "image": image
                }

                return f"Container created successfully: {container.name} ({container.id[:12]})"

            except Exception as e:
                return f"Error creating container: {str(e)}"

        @mcp_server.tool()
        async def execute_command(container_id: str, command: str) -> str:
            """Execute a command in a running container"""
            container = self._find_container(container_id)
            if not container:
                return f"Container {container_id} not found"

            try:
                result = container.exec_run(command, tty=True, stream=False)
                output = result.output.decode('utf-8', errors='replace')

                return f"Exit code: {result.exit_code}\nOutput:\n{output}"

            except Exception as e:
                return f"Error executing command: {str(e)}"

        @mcp_server.tool()
        async def list_containers() -> str:
            """List all active containers"""
            try:
                containers_info = []

                # Refresh active containers list
                current_containers = self.docker_client.containers.list(all=True)

                for container in current_containers:
                    try:
                        container_info = {
                            "id": container.id[:12],
                            "name": container.name,
                            "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                            "status": container.status,
                            "created": container.attrs.get('Created', 'Unknown'),
                            "ports": container.ports if hasattr(container, 'ports') else {}
                        }
                        containers_info.append(container_info)
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"Error getting container info: {e}")
                        continue

                if not containers_info:
                    return "No containers found"

                return json.dumps(containers_info, indent=2, default=str)

            except Exception as e:
                return f"Error listing containers: {str(e)}"

        @mcp_server.tool()
        async def upload_file(filename: str, content: str) -> str:
            """Upload a file to the shared workspace"""
            try:
                workspace_path = Path("/tmp/workspace")
                workspace_path.mkdir(exist_ok=True)

                file_path = workspace_path / filename

                # Ensure we don't write outside workspace
                if not str(file_path.resolve()).startswith(str(workspace_path.resolve())):
                    return f"Error: Invalid file path. Must be within workspace."

                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                return f"File uploaded successfully: {filename} ({len(content)} characters)"

            except Exception as e:
                return f"Error uploading file: {str(e)}"

        @mcp_server.tool()
        async def list_workspace_files() -> str:
            """List files in the shared workspace"""
            try:
                workspace_path = Path("/tmp/workspace")
                if not workspace_path.exists():
                    return "Workspace directory does not exist"

                files_info = []
                for item in workspace_path.rglob('*'):
                    if item.is_file():
                        try:
                            stat = item.stat()
                            files_info.append({
                                "name": str(item.relative_to(workspace_path)),
                                "size": stat.st_size,
                                "modified": time.ctime(stat.st_mtime)
                            })
                        except Exception:
                            continue

                return json.dumps(files_info, indent=2)

            except Exception as e:
                return f"Error listing workspace files: {str(e)}"

        @mcp_server.tool()
        async def stop_container(container_id: str) -> str:
            """Stop a running container (without removing it)"""
            container = self._find_container(container_id)
            if not container:
                return f"Container {container_id} not found"

            try:
                container.stop()
                return f"Container {container_id} stopped successfully"
            except Exception as e:
                return f"Error stopping container: {str(e)}"

        @mcp_server.tool()
        async def start_container(container_id: str) -> str:
            """Start a stopped container"""
            container = self._find_container(container_id)
            if not container:
                return f"Container {container_id} not found"

            try:
                container.start()
                return f"Container {container_id} started successfully"
            except Exception as e:
                return f"Error starting container: {str(e)}"

        @mcp_server.tool()
        async def restart_container(container_id: str) -> str:
            """Restart a container"""
            container = self._find_container(container_id)
            if not container:
                return f"Container {container_id} not found"

            try:
                container.restart()
                return f"Container {container_id} restarted successfully"
            except Exception as e:
                return f"Error restarting container: {str(e)}"

        @mcp_server.tool()
        async def delete_container(container_id: str) -> str:
            """Delete a container (stops and removes it)"""
            container = self._find_container(container_id)
            if not container:
                return f"Container {container_id} not found"

            try:
                container.stop()
                container.remove()

                # Remove from active containers
                if container.id in self.active_containers:
                    del self.active_containers[container.id]

                return f"Container {container_id} deleted successfully"
            except Exception as e:
                return f"Error deleting container: {str(e)}"

        @mcp_server.tool()
        async def get_container_logs(container_id: str, tail: int = 100) -> str:
            """Get logs from a container"""
            container = self._find_container(container_id)
            if not container:
                return f"Container {container_id} not found"

            try:
                logs = container.logs(tail=tail, timestamps=True)
                return logs.decode('utf-8', errors='replace')
            except Exception as e:
                return f"Error getting container logs: {str(e)}"

    def _find_container(self, container_id: str):
        """Find a container by ID or name"""
        try:
            # Try exact match first
            if container_id in self.active_containers:
                return self.active_containers[container_id]["container"]

            # Try to get from Docker directly
            try:
                return self.docker_client.containers.get(container_id)
            except docker.errors.NotFound:
                # Try partial ID match
                containers = self.docker_client.containers.list(all=True)
                for container in containers:
                    if container.id.startswith(container_id) or container.name == container_id:
                        return container
                return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error finding container: {e}")
            return None
