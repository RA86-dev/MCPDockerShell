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
                ["docker", "container", "inspect", container],
                capture_output=True,
                timeout=20,
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
                    nvidia_info = []
                    for line in result.stdout.strip().split("\n"):
                        if line.strip():
                            name, mem_total, mem_used, utilization = [
                                x.strip() for x in line.split(",")
                            ]
                            nvidia_info.append(
                                {
                                    "name": name,
                                    "memory_total_mb": int(mem_total),
                                    "memory_used_mb": int(mem_used),
                                    "utilization_percent": int(utilization),
                                }
                            )
                    status_info.append(
                        {"type": "NVIDIA", "gpus": nvidia_info, "available": True}
                    )
                else:
                    status_info.append(
                        {
                            "type": "NVIDIA",
                            "available": False,
                            "error": "nvidia-smi failed",
                        }
                    )
            except (
                subprocess.TimeoutExpired,
                FileNotFoundError,
                subprocess.SubprocessError,
            ):
                status_info.append(
                    {
                        "type": "NVIDIA",
                        "available": False,
                        "error": "nvidia-smi not found or failed",
                    }
                )

            # Check AMD ROCm status
            try:
                result = subprocess.run(
                    [
                        "rocm-smi",
                        "--showproductname",
                        "--showmeminfo",
                        "vram",
                        "--showuse",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if result.returncode == 0:
                    status_info.append(
                        {"type": "AMD_ROCm", "available": True, "info": "ROCm detected"}
                    )
                else:
                    status_info.append(
                        {
                            "type": "AMD_ROCm",
                            "available": False,
                            "error": "rocm-smi failed",
                        }
                    )
            except (
                subprocess.TimeoutExpired,
                FileNotFoundError,
                subprocess.SubprocessError,
            ):
                status_info.append(
                    {
                        "type": "AMD_ROCm",
                        "available": False,
                        "error": "rocm-smi not found",
                    }
                )

            return json.dumps(status_info, indent=2)

        @mcp_server.tool()
        async def create_container(
            image: str,
            name: str = None,
            command: str = None,
            environment: Dict[str, str] = None,
            ports: Dict[str, int] = None,
            use_gpu: bool = False,
        ) -> str:
            """Create and start a new Docker container that runs indefinitely"""
            if image not in self.allowed_images:
                return json.dumps({"error": f"Image '{image}' is not in the allowed list."})

            try:
                container_config = {
                    "image": image,
                    "detach": True,
                    "stdin_open": True,
                    "tty": True,
                    "working_dir": "/workspace",
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
                    else:
                        container_config["command"] = "/bin/sh"

                if environment:
                    container_config["environment"] = environment

                if ports:
                    container_config["ports"] = ports

                if use_gpu:
                    container_config["device_requests"] = [
                        docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])
                    ]

                # Create workspace volume
                workspace_path = Path(self.temp_dir) / "workspace"
                workspace_path.mkdir(parents=True, exist_ok=True)
                container_config["volumes"] = {
                    str(workspace_path): {"bind": "/workspace", "mode": "rw"}
                }

                container = self.docker_client.containers.run(**container_config)

                self.active_containers[container.id] = {
                    "container": container,
                    "name": name or container.name,
                    "created_at": time.time(),
                    "image": image,
                }

                return json.dumps({
                    "success": True,
                    "message": f"Container created successfully: {container.name} ({container.id[:12]})",
                    "container_id": container.id,
                    "container_name": container.name
                })

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error creating container: {e}")
                return json.dumps({"error": str(e)})

        @mcp_server.tool()
        async def execute_command(container_id: str, command: str) -> str:
            """Execute a command in a running container"""
            container = self._find_container(container_id)
            if not container:
                return json.dumps({"error": f"Container '{container_id}' not found."})

            try:
                result = container.exec_run(command, tty=True, stream=False)
                output = result.output.decode("utf-8", errors="replace")
                return json.dumps({
                    "exit_code": result.exit_code,
                    "output": output
                })
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error executing command in {container_id}: {e}")
                return json.dumps({"error": str(e)})

        @mcp_server.tool()
        async def list_containers() -> str:
            """List all active containers"""
            try:
                containers_info = []
                for container in self.docker_client.containers.list(all=True):
                    containers_info.append({
                        "id": container.id[:12],
                        "name": container.name,
                        "image": container.image.tags[0] if container.image.tags else container.image.id,
                        "status": container.status,
                    })
                return json.dumps(containers_info, indent=2)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error listing containers: {e}")
                return json.dumps({"error": str(e)})

        @mcp_server.tool()
        async def upload_file(filename: str, content: str) -> str:
            """Upload a file to the shared workspace"""
            try:
                workspace_path = Path(self.temp_dir) / "workspace"
                workspace_path.mkdir(parents=True, exist_ok=True)
                file_path = workspace_path / filename

                if not file_path.resolve().is_relative_to(workspace_path.resolve()):
                     return json.dumps({"error": "Invalid file path. Must be within workspace."})

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                return json.dumps({"success": True, "message": f"File '{filename}' uploaded successfully."})
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error uploading file: {e}")
                return json.dumps({"error": str(e)})

        @mcp_server.tool()
        async def list_workspace_files() -> str:
            """List files in the shared workspace"""
            try:
                workspace_path = Path(self.temp_dir) / "workspace"
                if not workspace_path.exists():
                    return json.dumps([])

                files_info = [
                    {
                        "name": str(item.relative_to(workspace_path)),
                        "size": item.stat().st_size,
                        "modified": time.ctime(item.stat().st_mtime),
                    }
                    for item in workspace_path.rglob("*") if item.is_file()
                ]
                return json.dumps(files_info, indent=2)
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error listing workspace files: {e}")
                return json.dumps({"error": str(e)})

        @mcp_server.tool()
        async def stop_container(container_id: str) -> str:
            """Stop a running container"""
            container = self._find_container(container_id)
            if not container:
                return json.dumps({"error": f"Container '{container_id}' not found."})
            try:
                container.stop()
                return json.dumps({"success": True, "message": f"Container '{container_id}' stopped."})
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error stopping container {container_id}: {e}")
                return json.dumps({"error": str(e)})

        @mcp_server.tool()
        async def start_container(container_id: str) -> str:
            """Start a stopped container"""
            container = self._find_container(container_id)
            if not container:
                return json.dumps({"error": f"Container '{container_id}' not found."})
            try:
                container.start()
                return json.dumps({"success": True, "message": f"Container '{container_id}' started."})
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error starting container {container_id}: {e}")
                return json.dumps({"error": str(e)})

        @mcp_server.tool()
        async def restart_container(container_id: str) -> str:
            """Restart a container"""
            container = self._find_container(container_id)
            if not container:
                return json.dumps({"error": f"Container '{container_id}' not found."})
            try:
                container.restart()
                return json.dumps({"success": True, "message": f"Container '{container_id}' restarted."})
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error restarting container {container_id}: {e}")
                return json.dumps({"error": str(e)})

        @mcp_server.tool()
        async def delete_container(container_id: str) -> str:
            """Delete a container"""
            container = self._find_container(container_id)
            if not container:
                return json.dumps({"error": f"Container '{container_id}' not found."})
            try:
                container.remove(force=True)
                if container.id in self.active_containers:
                    del self.active_containers[container.id]
                return json.dumps({"success": True, "message": f"Container '{container_id}' deleted."})
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error deleting container {container_id}: {e}")
                return json.dumps({"error": str(e)})

        @mcp_server.tool()
        async def get_container_logs(container_id: str, tail: int = 100) -> str:
            """Get logs from a container"""
            container = self._find_container(container_id)
            if not container:
                return json.dumps({"error": f"Container '{container_id}' not found."})
            try:
                logs = container.logs(tail=tail, timestamps=True).decode("utf-8", errors="replace")
                return json.dumps({"logs": logs})
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error getting logs for {container_id}: {e}")
                return json.dumps({"error": str(e)})

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
                    if (
                        container.id.startswith(container_id)
                        or container.name == container_id
                    ):
                        return container
                return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error finding container: {e}")
            return None
