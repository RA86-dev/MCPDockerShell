"""
Monitoring and metrics tools for system and container performance
"""
import json
import time
import psutil
import docker
from typing import Dict, Any, List
from collections import defaultdict
from datetime import datetime

class MonitoringTools:
    """System and container monitoring functionality"""
    
    def __init__(self, docker_client, active_containers: dict, logger=None):
        self.docker_client = docker_client
        self.active_containers = active_containers
        self.logger = logger
        self.monitoring_data = defaultdict(list)
        self.performance_metrics = {
            "container_stats": {},
            "system_stats": {},
            "operation_times": [],
            "api_response_times": [],
            "error_rates": defaultdict(int),
            "resource_usage": defaultdict(list),
        }
        
    def register_tools(self, mcp_server):
        """Register monitoring tools with the MCP server"""
        
        @mcp_server.tool()
        async def monitor_system_resources() -> str:
            """Monitor system CPU, memory, disk, and network usage"""
            try:
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_count = psutil.cpu_count()
                cpu_freq = psutil.cpu_freq()
                
                # Memory usage
                memory = psutil.virtual_memory()
                swap = psutil.swap_memory()
                
                # Disk usage
                disk_usage = []
                for partition in psutil.disk_partitions():
                    try:
                        partition_usage = psutil.disk_usage(partition.mountpoint)
                        disk_usage.append({
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "total_gb": round(partition_usage.total / (1024**3), 2),
                            "used_gb": round(partition_usage.used / (1024**3), 2),
                            "free_gb": round(partition_usage.free / (1024**3), 2),
                            "percent_used": round((partition_usage.used / partition_usage.total) * 100, 1)
                        })
                    except PermissionError:
                        continue
                
                # Network usage
                network = psutil.net_io_counters()
                
                system_info = {
                    "timestamp": datetime.now().isoformat(),
                    "cpu": {
                        "percent": cpu_percent,
                        "count": cpu_count,
                        "frequency_mhz": cpu_freq.current if cpu_freq else None
                    },
                    "memory": {
                        "total_gb": round(memory.total / (1024**3), 2),
                        "available_gb": round(memory.available / (1024**3), 2),
                        "used_gb": round(memory.used / (1024**3), 2),
                        "percent": memory.percent
                    },
                    "swap": {
                        "total_gb": round(swap.total / (1024**3), 2),
                        "used_gb": round(swap.used / (1024**3), 2),
                        "percent": swap.percent
                    },
                    "disk": disk_usage,
                    "network": {
                        "bytes_sent": network.bytes_sent,
                        "bytes_recv": network.bytes_recv,
                        "packets_sent": network.packets_sent,
                        "packets_recv": network.packets_recv
                    }
                }
                
                # Store for historical tracking
                self.performance_metrics["system_stats"][datetime.now().isoformat()] = system_info
                
                return json.dumps(system_info, indent=2)
                
            except Exception as e:
                return f"Error monitoring system resources: {str(e)}"

        @mcp_server.tool()
        async def monitor_container_performance(container_id: str) -> str:
            """Monitor performance metrics for a specific container"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"
                
                # Get container stats
                stats = container.stats(stream=False)
                
                # Calculate CPU usage
                cpu_stats = stats.get('cpu_stats', {})
                precpu_stats = stats.get('precpu_stats', {})
                
                cpu_usage = 0.0
                if cpu_stats.get('cpu_usage') and precpu_stats.get('cpu_usage'):
                    cpu_delta = cpu_stats['cpu_usage']['total_usage'] - precpu_stats['cpu_usage']['total_usage']
                    system_delta = cpu_stats.get('system_cpu_usage', 0) - precpu_stats.get('system_cpu_usage', 0)
                    online_cpus = cpu_stats.get('online_cpus', len(cpu_stats.get('cpu_usage', {}).get('percpu_usage', [1])))
                    
                    if system_delta > 0:
                        cpu_usage = (cpu_delta / system_delta) * online_cpus * 100.0
                
                # Memory usage
                memory_stats = stats.get('memory_stats', {})
                memory_usage = memory_stats.get('usage', 0)
                memory_limit = memory_stats.get('limit', 0)
                memory_percent = (memory_usage / memory_limit * 100) if memory_limit else 0
                
                # Network I/O
                networks = stats.get('networks', {})
                network_rx = sum(net.get('rx_bytes', 0) for net in networks.values())
                network_tx = sum(net.get('tx_bytes', 0) for net in networks.values())
                
                # Block I/O
                blkio_stats = stats.get('blkio_stats', {})
                blk_read = 0
                blk_write = 0
                
                for entry in blkio_stats.get('io_service_bytes_recursive', []):
                    if entry.get('op') == 'Read':
                        blk_read += entry.get('value', 0)
                    elif entry.get('op') == 'Write':
                        blk_write += entry.get('value', 0)
                
                container_performance = {
                    "container_id": container_id[:12],
                    "name": container.name,
                    "timestamp": datetime.now().isoformat(),
                    "cpu": {
                        "usage_percent": round(cpu_usage, 2)
                    },
                    "memory": {
                        "usage_bytes": memory_usage,
                        "usage_mb": round(memory_usage / (1024**2), 2),
                        "limit_bytes": memory_limit,
                        "limit_mb": round(memory_limit / (1024**2), 2),
                        "usage_percent": round(memory_percent, 2)
                    },
                    "network": {
                        "rx_bytes": network_rx,
                        "tx_bytes": network_tx,
                        "rx_mb": round(network_rx / (1024**2), 2),
                        "tx_mb": round(network_tx / (1024**2), 2)
                    },
                    "block_io": {
                        "read_bytes": blk_read,
                        "write_bytes": blk_write,
                        "read_mb": round(blk_read / (1024**2), 2),
                        "write_mb": round(blk_write / (1024**2), 2)
                    }
                }
                
                # Store for historical tracking
                self.performance_metrics["container_stats"][container_id] = container_performance
                
                return json.dumps(container_performance, indent=2)
                
            except Exception as e:
                return f"Error monitoring container performance: {str(e)}"

        @mcp_server.tool()
        async def get_server_status() -> str:
            """Get comprehensive server status and health information"""
            try:
                # Docker status
                docker_info = self.docker_client.info()
                
                # Active containers count
                containers = self.docker_client.containers.list(all=True)
                running_containers = len([c for c in containers if c.status == 'running'])
                total_containers = len(containers)
                
                # System uptime
                boot_time = psutil.boot_time()
                uptime_seconds = time.time() - boot_time
                uptime_hours = uptime_seconds / 3600
                
                # Load averages (Unix-like systems only)
                load_avg = None
                try:
                    load_avg = psutil.getloadavg()
                except AttributeError:
                    pass  # Windows doesn't have load averages
                
                status_info = {
                    "timestamp": datetime.now().isoformat(),
                    "system": {
                        "uptime_hours": round(uptime_hours, 2),
                        "boot_time": datetime.fromtimestamp(boot_time).isoformat(),
                        "load_average": load_avg,
                        "platform": psutil.LINUX or psutil.MACOS or psutil.WINDOWS
                    },
                    "docker": {
                        "version": docker_info.get('ServerVersion', 'Unknown'),
                        "containers_running": running_containers,
                        "containers_total": total_containers,
                        "images_count": len(self.docker_client.images.list()),
                        "storage_driver": docker_info.get('Driver', 'Unknown'),
                        "kernel_version": docker_info.get('KernelVersion', 'Unknown')
                    },
                    "resources": {
                        "cpu_count": psutil.cpu_count(),
                        "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
                        "disk_total_gb": round(psutil.disk_usage('/').total / (1024**3), 2) if psutil.disk_usage('/') else 0
                    },
                    "active_services": {
                        "mcp_server": True,
                        "docker_daemon": True,
                        "monitoring": True
                    }
                }
                
                return json.dumps(status_info, indent=2)
                
            except Exception as e:
                return f"Error getting server status: {str(e)}"

        @mcp_server.tool()
        async def create_container_backup(container_id: str, backup_name: str = None) -> str:
            """Create a backup of a container and its data"""
            try:
                container = self._find_container(container_id)
                if not container:
                    return f"Container {container_id} not found"
                
                if not backup_name:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"{container.name}_backup_{timestamp}"
                
                # Commit the container to create an image
                image = container.commit(repository=backup_name, tag="latest")
                
                backup_info = {
                    "backup_name": backup_name,
                    "original_container": container_id,
                    "image_id": image.id,
                    "created": datetime.now().isoformat(),
                    "size_mb": round(image.attrs.get('Size', 0) / (1024**2), 2)
                }
                
                return f"Container backup created: {json.dumps(backup_info, indent=2)}"
                
            except Exception as e:
                return f"Error creating container backup: {str(e)}"

        @mcp_server.tool()
        async def create_workspace_backup(backup_name: str = None) -> str:
            """Create a backup of the shared workspace"""
            try:
                import tarfile
                from pathlib import Path
                
                workspace_path = Path("/tmp/workspace")
                if not workspace_path.exists():
                    return "Workspace directory does not exist"
                
                if not backup_name:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    backup_name = f"workspace_backup_{timestamp}.tar.gz"
                
                backup_path = Path("/tmp") / backup_name
                
                with tarfile.open(backup_path, "w:gz") as tar:
                    tar.add(workspace_path, arcname="workspace")
                
                backup_size = backup_path.stat().st_size
                
                backup_info = {
                    "backup_name": backup_name,
                    "backup_path": str(backup_path),
                    "created": datetime.now().isoformat(),
                    "size_bytes": backup_size,
                    "size_mb": round(backup_size / (1024**2), 2)
                }
                
                return f"Workspace backup created: {json.dumps(backup_info, indent=2)}"
                
            except Exception as e:
                return f"Error creating workspace backup: {str(e)}"

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