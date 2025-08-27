"""
Notification system for MCP Docker Server using Ntfy.sh
Provides system monitoring notifications and tool execution alerts
"""
import requests
import json
import time
import psutil
import threading
from datetime import datetime
from collections import defaultdict


class ntfyClient:
    """Enhanced Ntfy.sh client for notifications"""
    
    def __init__(self, base_url: str, default_topic: str = "mcpdocker"):
        self.base_url = base_url.rstrip('/')
        self.default_topic = default_topic
        self.session = requests.Session()
        self.session.timeout = 10
        
    def send_message(
        self,
        title: str = "MCP Docker Server",
        priority: str = "default", 
        tags: list = None,
        description: str = "No description available",
        topic: str = None,
        actions: list = None,
        click_url: str = None,
        attach_url: str = None,
        icon_url: str = None
    ) -> bool:
        """Send a notification via Ntfy.sh with enhanced options"""
        try:
            if tags is None:
                tags = ["mcpdocker"]
            if topic is None:
                topic = self.default_topic
                
            url = f"{self.base_url}/{topic}"
            
            headers = {
                "Title": title,
                "Priority": priority,
                "Tags": ",".join(tags) if isinstance(tags, list) else str(tags),
                "Content-Type": "text/plain"
            }
            
            # Add optional headers
            if actions:
                headers["Actions"] = json.dumps(actions)
            if click_url:
                headers["Click"] = click_url
            if attach_url:
                headers["Attach"] = attach_url
            if icon_url:
                headers["Icon"] = icon_url
            
            response = self.session.post(
                url,
                data=description,
                headers=headers
            )
            
            if response.status_code == 200:
                return True
            else:
                print(f"Ntfy notification failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending notification: {e}")
            return False
    
    def send_system_alert(self, metric: str, value: float, threshold: float, severity: str = "warning"):
        """Send system resource alert"""
        priority_map = {
            "info": "low",
            "warning": "default", 
            "critical": "high",
            "emergency": "max"
        }
        
        emoji_map = {
            "cpu": "🖥️",
            "memory": "💾",
            "disk": "💿",
            "network": "🌐"
        }
        
        title = f"{emoji_map.get(metric, '⚠️')} System {severity.title()}: {metric.title()}"
        description = f"{metric.title()} usage is at {value}%, exceeding threshold of {threshold}%"
        
        self.send_message(
            title=title,
            description=description,
            priority=priority_map.get(severity, "default"),
            tags=["system", "monitoring", severity, metric]
        )
    
    def send_tool_notification(self, tool_name: str, status: str, details: str = ""):
        """Send tool execution notification"""
        status_emoji = {
            "started": "🚀",
            "completed": "✅", 
            "failed": "❌",
            "warning": "⚠️"
        }
        
        title = f"{status_emoji.get(status, '🔧')} Tool {status.title()}: {tool_name}"
        description = f"Tool '{tool_name}' {status}" + (f" - {details}" if details else "")
        
        priority = "high" if status == "failed" else "low"
        
        self.send_message(
            title=title,
            description=description,
            priority=priority,
            tags=["tools", "execution", status]
        )


class NotificationTools:
    """Notification and monitoring tools for MCP Docker Server"""
    
    def __init__(self, ntfy_url: str, logger=None, monitoring_interval: int = 7200):
        self.ntfy_client = ntfyClient(ntfy_url)
        self.logger = logger
        self.monitoring_interval = monitoring_interval  # Default 2 hours in seconds
        self.monitoring_active = False
        self.monitoring_thread = None
        self.tool_execution_log = defaultdict(int)
        self.last_system_check = None
        
        # Thresholds for system alerts
        self.thresholds = {
            "cpu": 85.0,
            "memory": 90.0,
            "disk": 95.0
        }
        
        # Start monitoring when initialized
        self.start_monitoring()
    
    def register_tools(self, mcp_server):
        """Register notification tools with the MCP server"""
        
        @mcp_server.tool()
        async def send_test_notification(
            title: str = "Test Notification", 
            message: str = "This is a test from MCP Docker Server",
            priority: str = "low"
        ) -> str:
            """Send a test notification via Ntfy.sh"""
            try:
                success = self.ntfy_client.send_message(
                    title=title,
                    description=message,
                    priority=priority,
                    tags=["test"]
                )
                return f"Test notification sent: {success}"
            except Exception as e:
                return f"Error sending test notification: {str(e)}"
        
        @mcp_server.tool()
        async def configure_monitoring_thresholds(
            cpu_threshold: float = None,
            memory_threshold: float = None, 
            disk_threshold: float = None
        ) -> str:
            """Configure system monitoring alert thresholds"""
            try:
                if cpu_threshold is not None:
                    self.thresholds["cpu"] = cpu_threshold
                if memory_threshold is not None:
                    self.thresholds["memory"] = memory_threshold
                if disk_threshold is not None:
                    self.thresholds["disk"] = disk_threshold
                    
                return f"Monitoring thresholds updated: {json.dumps(self.thresholds, indent=2)}"
            except Exception as e:
                return f"Error configuring thresholds: {str(e)}"
        
        @mcp_server.tool()
        async def get_notification_status() -> str:
            """Get current notification system status"""
            try:
                status = {
                    "ntfy_server": self.ntfy_client.base_url,
                    "monitoring_active": self.monitoring_active,
                    "monitoring_interval_hours": self.monitoring_interval / 3600,
                    "last_system_check": self.last_system_check.isoformat() if self.last_system_check else None,
                    "thresholds": self.thresholds,
                    "tool_executions_today": dict(self.tool_execution_log)
                }
                return json.dumps(status, indent=2)
            except Exception as e:
                return f"Error getting notification status: {str(e)}"
        
        @mcp_server.tool()
        async def send_system_report() -> str:
            """Send immediate system resource report"""
            try:
                report = self._generate_system_report()
                
                success = self.ntfy_client.send_message(
                    title="📊 System Resource Report",
                    description=report,
                    priority="low",
                    tags=["system", "report", "manual"]
                )
                
                return f"System report sent: {success}\n\nReport content:\n{report}"
            except Exception as e:
                return f"Error sending system report: {str(e)}"
        
        @mcp_server.tool()
        async def restart_monitoring() -> str:
            """Restart the system monitoring service"""
            try:
                self.stop_monitoring()
                time.sleep(1)
                self.start_monitoring()
                return "System monitoring restarted successfully"
            except Exception as e:
                return f"Error restarting monitoring: {str(e)}"
    
    def start_monitoring(self):
        """Start background system monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self.monitoring_thread.start()
            
            # Send startup notification
            self.ntfy_client.send_message(
                title="🚀 MCP Docker Server Started",
                description=f"System monitoring started with {self.monitoring_interval/3600}h intervals",
                priority="low",
                tags=["startup", "system"]
            )
            
            if self.logger:
                self.logger.info(f"Notification monitoring started with {self.monitoring_interval}s intervals")
    
    def stop_monitoring(self):
        """Stop background system monitoring"""
        if self.monitoring_active:
            self.monitoring_active = False
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            if self.logger:
                self.logger.info("Notification monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop running in background thread"""
        while self.monitoring_active:
            try:
                self._check_system_resources()
                self.last_system_check = datetime.now()
                
                # Sleep in small intervals to allow clean shutdown
                for _ in range(int(self.monitoring_interval)):
                    if not self.monitoring_active:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait a minute before retrying
    
    def _check_system_resources(self):
        """Check system resources and send alerts if thresholds exceeded"""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.thresholds["cpu"]:
                self.ntfy_client.send_system_alert("cpu", cpu_percent, self.thresholds["cpu"], "warning")
            
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.thresholds["memory"]:
                self.ntfy_client.send_system_alert("memory", memory.percent, self.thresholds["memory"], "warning")
            
            # Check disk usage for root partition
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > self.thresholds["disk"]:
                self.ntfy_client.send_system_alert("disk", disk_percent, self.thresholds["disk"], "critical")
            
            # Send periodic system report (every monitoring interval)
            report = self._generate_system_report()
            self.ntfy_client.send_message(
                title="📊 Periodic System Report",
                description=report,
                priority="low",
                tags=["system", "report", "periodic"]
            )
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error checking system resources: {e}")
    
    def _generate_system_report(self) -> str:
        """Generate formatted system resource report"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            report = f"""System Resources Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

🖥️ CPU Usage: {cpu_percent:.1f}% (threshold: {self.thresholds['cpu']}%)
💾 Memory Usage: {memory.percent:.1f}% ({memory.used/1024**3:.1f}GB / {memory.total/1024**3:.1f}GB)
💿 Disk Usage: {(disk.used/disk.total)*100:.1f}% ({disk.used/1024**3:.1f}GB / {disk.total/1024**3:.1f}GB)

Server Uptime: {datetime.now() - datetime.fromtimestamp(psutil.boot_time())}
"""
            return report
            
        except Exception as e:
            return f"Error generating system report: {e}"
    
    def notify_tool_execution(self, tool_name: str, status: str, details: str = "", duration: float = None):
        """Notify about tool execution - called by main server"""
        try:
            # Log tool execution
            today = datetime.now().strftime('%Y-%m-%d')
            self.tool_execution_log[f"{today}_{tool_name}"] += 1
            
            # Add duration to details if provided
            if duration:
                details = f"{details} (took {duration:.2f}s)" if details else f"Execution time: {duration:.2f}s"
            
            self.ntfy_client.send_tool_notification(tool_name, status, details)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error notifying tool execution: {e}")
    
    def cleanup(self):
        """Clean up resources on shutdown"""
        self.stop_monitoring()
        
        # Send shutdown notification
        try:
            self.ntfy_client.send_message(
                title="🛑 MCP Docker Server Shutting Down",
                description="Server is shutting down gracefully",
                priority="low",
                tags=["shutdown", "system"]
            )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error sending shutdown notification: {e}")