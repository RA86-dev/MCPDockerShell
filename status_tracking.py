import subprocess
import psutil
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="System Status Tracker")

def get_nvidia_status():
    """Get NVIDIA GPU status using nvidia-smi"""
    try:
        result = subprocess.run(['nvidia-smi', '--query-gpu=name,driver_version,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw', '--format=csv,noheader,nounits'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            gpus = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = [p.strip() for p in line.split(',')]
                    gpus.append({
                        'name': parts[0],
                        'driver_version': parts[1],
                        'temperature': parts[2],
                        'utilization': parts[3],
                        'memory_used': parts[4],
                        'memory_total': parts[5],
                        'power_draw': parts[6]
                    })
            return {'status': 'available', 'gpus': gpus}
        else:
            return {'status': 'error', 'message': 'nvidia-smi failed'}
    except FileNotFoundError:
        return {'status': 'not_available', 'message': 'NVIDIA drivers not installed'}
    except subprocess.TimeoutExpired:
        return {'status': 'timeout', 'message': 'nvidia-smi timed out'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_system_status():
    """Get general system status"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu': {
                'usage_percent': cpu_percent,
                'count': psutil.cpu_count(),
                'count_logical': psutil.cpu_count(logical=True)
            },
            'memory': {
                'total': memory.total,
                'available': memory.available,
                'used': memory.used,
                'percentage': memory.percent
            },
            'disk': {
                'total': disk.total,
                'used': disk.used,
                'free': disk.free,
                'percentage': (disk.used / disk.total) * 100
            },
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        return {'error': str(e)}

@app.get('/', response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page"""
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Status Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card h2 {
            color: #333;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
            font-size: 1.3em;
        }
        
        .status-item {
            margin: 15px 0;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        
        .status-label {
            font-weight: 600;
            color: #495057;
        }
        
        .status-value {
            font-size: 1.1em;
            color: #212529;
            margin-left: 10px;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            margin-top: 5px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        
        .progress-low { background: #28a745; }
        .progress-medium { background: #ffc107; }
        .progress-high { background: #dc3545; }
        
        .gpu-grid {
            display: grid;
            gap: 15px;
        }
        
        .gpu-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 50px;
            padding: 15px 20px;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s ease;
            font-size: 1em;
        }
        
        .refresh-btn:hover {
            background: #5a6fd8;
            transform: scale(1.05);
        }
        
        .loading {
            text-align: center;
            color: #6c757d;
            font-style: italic;
        }
        
        .error {
            color: #dc3545;
            background: #f8d7da;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #f5c6cb;
        }
        
        .success {
            color: #155724;
            background: #d4edda;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #c3e6cb;
        }
        
        @media (max-width: 768px) {
            .grid {
                grid-template-columns: 1fr;
            }
            .header h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🖥️ System Status Dashboard</h1>
            <p>Real-time monitoring of your system resources</p>
        </div>
        
        <div class="grid">
            <!-- System Status Card -->
            <div class="card">
                <h2>💻 System Resources</h2>
                <div id="system-status" class="loading">Loading system status...</div>
            </div>
            
            <!-- NVIDIA GPU Card -->
            <div class="card">
                <h2>🎮 NVIDIA GPU Status</h2>
                <div id="gpu-status" class="loading">Loading GPU status...</div>
            </div>
            
            <!-- Docker Containers Card -->
            <div class="card">
                <h2>🐳 Docker Status</h2>
                <div id="docker-status" class="loading">Loading Docker status...</div>
            </div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="refreshAll()">🔄 Refresh</button>
    
    <script>
        function formatBytes(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
        
        function getProgressClass(percentage) {
            if (percentage < 60) return 'progress-low';
            if (percentage < 85) return 'progress-medium';
            return 'progress-high';
        }
        
        async function loadSystemStatus() {
            try {
                const response = await fetch('/api/system');
                const data = await response.json();
                
                if (data.error) {
                    document.getElementById('system-status').innerHTML = 
                        '<div class="error">Error: ' + data.error + '</div>';
                    return;
                }
                
                const html = `
                    <div class="status-item">
                        <span class="status-label">CPU Usage:</span>
                        <span class="status-value">${data.cpu.usage_percent}%</span>
                        <div class="progress-bar">
                            <div class="progress-fill ${getProgressClass(data.cpu.usage_percent)}" 
                                 style="width: ${data.cpu.usage_percent}%"></div>
                        </div>
                    </div>
                    <div class="status-item">
                        <span class="status-label">CPU Cores:</span>
                        <span class="status-value">${data.cpu.count} physical, ${data.cpu.count_logical} logical</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Memory:</span>
                        <span class="status-value">${formatBytes(data.memory.used)} / ${formatBytes(data.memory.total)} (${data.memory.percentage}%)</span>
                        <div class="progress-bar">
                            <div class="progress-fill ${getProgressClass(data.memory.percentage)}" 
                                 style="width: ${data.memory.percentage}%"></div>
                        </div>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Disk:</span>
                        <span class="status-value">${formatBytes(data.disk.used)} / ${formatBytes(data.disk.total)} (${data.disk.percentage.toFixed(1)}%)</span>
                        <div class="progress-bar">
                            <div class="progress-fill ${getProgressClass(data.disk.percentage)}" 
                                 style="width: ${data.disk.percentage}%"></div>
                        </div>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Last Updated:</span>
                        <span class="status-value">${new Date(data.timestamp).toLocaleString()}</span>
                    </div>
                `;
                
                document.getElementById('system-status').innerHTML = html;
            } catch (error) {
                document.getElementById('system-status').innerHTML = 
                    '<div class="error">Failed to load system status: ' + error.message + '</div>';
            }
        }
        
        async function loadGPUStatus() {
            try {
                const response = await fetch('/api/nvidia');
                const data = await response.json();
                
                let html = '';
                
                if (data.status === 'available') {
                    html = '<div class="success">✅ NVIDIA GPU(s) detected</div>';
                    html += '<div class="gpu-grid">';
                    
                    data.gpus.forEach((gpu, index) => {
                        html += `
                            <div class="gpu-card">
                                <h3>GPU ${index + 1}: ${gpu.name}</h3>
                                <div class="status-item">
                                    <span class="status-label">Driver Version:</span>
                                    <span class="status-value">${gpu.driver_version}</span>
                                </div>
                                <div class="status-item">
                                    <span class="status-label">Temperature:</span>
                                    <span class="status-value">${gpu.temperature}°C</span>
                                </div>
                                <div class="status-item">
                                    <span class="status-label">Utilization:</span>
                                    <span class="status-value">${gpu.utilization}%</span>
                                    <div class="progress-bar">
                                        <div class="progress-fill ${getProgressClass(gpu.utilization)}" 
                                             style="width: ${gpu.utilization}%"></div>
                                    </div>
                                </div>
                                <div class="status-item">
                                    <span class="status-label">Memory:</span>
                                    <span class="status-value">${gpu.memory_used} MB / ${gpu.memory_total} MB</span>
                                    <div class="progress-bar">
                                        <div class="progress-fill ${getProgressClass((gpu.memory_used / gpu.memory_total) * 100)}" 
                                             style="width: ${(gpu.memory_used / gpu.memory_total) * 100}%"></div>
                                    </div>
                                </div>
                                <div class="status-item">
                                    <span class="status-label">Power Draw:</span>
                                    <span class="status-value">${gpu.power_draw} W</span>
                                </div>
                            </div>
                        `;
                    });
                    html += '</div>';
                } else if (data.status === 'not_available') {
                    html = '<div class="error">❌ NVIDIA drivers not installed</div>';
                } else {
                    html = '<div class="error">⚠️ ' + data.message + '</div>';
                }
                
                document.getElementById('gpu-status').innerHTML = html;
            } catch (error) {
                document.getElementById('gpu-status').innerHTML = 
                    '<div class="error">Failed to load GPU status: ' + error.message + '</div>';
            }
        }
        
        async function loadDockerStatus() {
            try {
                const response = await fetch('/api/docker');
                const data = await response.json();
                
                let html = '';
                if (data.error) {
                    html = '<div class="error">⚠️ ' + data.error + '</div>';
                } else {
                    html = `
                        <div class="success">✅ Docker is running</div>
                        <div class="status-item">
                            <span class="status-label">Total Containers:</span>
                            <span class="status-value">${data.containers.total}</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Running:</span>
                            <span class="status-value">${data.containers.running}</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Stopped:</span>
                            <span class="status-value">${data.containers.stopped}</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Images:</span>
                            <span class="status-value">${data.images}</span>
                        </div>
                        <div class="status-item">
                            <span class="status-label">Docker Version:</span>
                            <span class="status-value">${data.version}</span>
                        </div>
                    `;
                }
                
                document.getElementById('docker-status').innerHTML = html;
            } catch (error) {
                document.getElementById('docker-status').innerHTML = 
                    '<div class="error">Failed to load Docker status: ' + error.message + '</div>';
            }
        }
        
        function refreshAll() {
            document.getElementById('system-status').innerHTML = '<div class="loading">Refreshing...</div>';
            document.getElementById('gpu-status').innerHTML = '<div class="loading">Refreshing...</div>';
            document.getElementById('docker-status').innerHTML = '<div class="loading">Refreshing...</div>';
            
            loadSystemStatus();
            loadGPUStatus();
            loadDockerStatus();
        }
        
        // Load data when page loads
        window.onload = function() {
            loadSystemStatus();
            loadGPUStatus();
            loadDockerStatus();
        };
        
        // Auto refresh every 30 seconds
        setInterval(refreshAll, 30000);
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

@app.get('/api/system')
async def system_status():
    """API endpoint for system status"""
    return get_system_status()

@app.get('/api/nvidia')
async def nvidia_status():
    """API endpoint for NVIDIA GPU status"""
    return get_nvidia_status()

@app.get('/api/docker')
async def docker_status():
    """API endpoint for Docker status"""
    try:
        # Check if Docker is running
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return {'error': 'Docker is not running or not accessible'}
        
        # Get container stats
        containers_result = subprocess.run(['docker', 'ps', '-a', '--format', 'table {{.Status}}'], 
                                         capture_output=True, text=True, timeout=10)
        containers_lines = containers_result.stdout.strip().split('\n')[1:]  # Skip header
        
        running = sum(1 for line in containers_lines if line.startswith('Up'))
        stopped = len(containers_lines) - running
        
        # Get image count
        images_result = subprocess.run(['docker', 'images', '-q'], capture_output=True, text=True, timeout=10)
        image_count = len([line for line in images_result.stdout.strip().split('\n') if line])
        
        # Get Docker version
        version_result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=10)
        version = version_result.stdout.strip() if version_result.returncode == 0 else 'Unknown'
        
        return {
            'containers': {
                'total': len(containers_lines),
                'running': running,
                'stopped': stopped
            },
            'images': image_count,
            'version': version
        }
        
    except FileNotFoundError:
        return {'error': 'Docker not installed'}
    except subprocess.TimeoutExpired:
        return {'error': 'Docker commands timed out'}
    except Exception as e:
        return {'error': str(e)}

def main():
    """Main function to start the server"""
    print("🚀 Starting System Status Dashboard...")
    print("📊 Dashboard will be available at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=7999)