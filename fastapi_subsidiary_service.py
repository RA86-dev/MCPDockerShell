from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
import json
import os
from datetime import datetime
import httpx
from main import MCPDockerServer

# Initialize FastAPI app
app = FastAPI(title="MCP Docker AI Interface", version="1.0.0")
templates = Jinja2Templates(directory="templates")

# Security
security = HTTPBearer()

# Global MCP Docker server instance
docker_server = None

class AIProvider(BaseModel):
    name: str
    api_key: str
    base_url: str
    model: str

class ChatMessage(BaseModel):
    role: str
    content: str
    timestamp: Optional[datetime] = None

class AIResponse(BaseModel):
    success: bool
    content: str
    error: Optional[str] = None

class DockerOperation(BaseModel):
    operation: str
    parameters: Dict
    result: Optional[str] = None

# In-memory storage (in production, use a proper database)
ai_providers: Dict[str, AIProvider] = {}
chat_history: List[ChatMessage] = []
operation_logs: List[DockerOperation] = []

@app.on_event("startup")
async def startup_event():
    """Initialize the MCP Docker server on startup"""
    global docker_server
    docker_server = MCPDockerServer()
    
    # Create templates directory if it doesn't exist
    os.makedirs("templates", exist_ok=True)
    os.makedirs("static", exist_ok=True)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    if docker_server:
        await docker_server.cleanup()

# AI Provider Management
@app.post("/api/providers")
async def add_ai_provider(provider: AIProvider):
    """Add a new AI provider configuration"""
    ai_providers[provider.name] = provider
    return {"message": f"AI provider {provider.name} added successfully"}

@app.get("/api/providers")
async def list_ai_providers():
    """List all configured AI providers"""
    return {name: {"name": p.name, "base_url": p.base_url, "model": p.model} 
            for name, p in ai_providers.items()}

@app.delete("/api/providers/{provider_name}")
async def remove_ai_provider(provider_name: str):
    """Remove an AI provider"""
    if provider_name in ai_providers:
        del ai_providers[provider_name]
        return {"message": f"AI provider {provider_name} removed"}
    raise HTTPException(status_code=404, detail="Provider not found")

# Docker Operations API
@app.post("/api/docker/containers")
async def create_container(
    image: str, 
    name: Optional[str] = None, 
    ports: Optional[Dict[int, int]] = None,
    use_gpu: bool = False
):
    """Create a new Docker container"""
    if not docker_server:
        raise HTTPException(status_code=500, detail="Docker server not initialized")
    
    try:
        # Validate image is allowed
        if image not in docker_server.allowed_images:
            raise HTTPException(status_code=400, detail=f"Image '{image}' not allowed")
        
        # Check GPU request
        if use_gpu and not docker_server.gpu_available:
            raise HTTPException(status_code=400, detail="GPU requested but NVIDIA GPU support is not available")
        
        container_name = name or f"mcpdocker_{len(docker_server.active_containers)}"
        
        # Create volume mount for file sharing
        volumes = {
            docker_server.temp_dir: {'bind': '/workspace', 'mode': 'rw'}
        }
        
        # Default command to keep container running
        default_command = "tail -f /dev/null"
        
        # GPU configuration
        device_requests = []
        if use_gpu and docker_server.gpu_available:
            import docker.types
            device_requests = [docker.types.DeviceRequest(count=-1, capabilities=[['gpu']])]
        
        container = docker_server.docker_client.containers.run(
            image,
            command=default_command,
            name=container_name,
            detach=True,
            ports=ports or {},
            environment={},
            volumes=volumes,
            working_dir="/workspace",
            tty=True,
            stdin_open=True,
            device_requests=device_requests
        )
        
        docker_server.active_containers[container.id] = container
        gpu_status = " (GPU enabled)" if use_gpu else ""
        result = f"Container {container_name} ({container.id[:12]}) created and started{gpu_status}"
        
        operation = DockerOperation(
            operation="create_container",
            parameters={"image": image, "name": name, "ports": ports, "use_gpu": use_gpu},
            result=result
        )
        operation_logs.append(operation)
        
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/docker/containers")
async def list_containers():
    """List all Docker containers"""
    if not docker_server:
        raise HTTPException(status_code=500, detail="Docker server not initialized")
    
    try:
        containers = []
        for container_id, container in docker_server.active_containers.items():
            try:
                container.reload()
                containers.append({
                    "id": container_id[:12],
                    "name": container.name,
                    "status": container.status,
                    "image": container.image.tags[0] if container.image.tags else "unknown"
                })
            except:
                containers.append({
                    "id": container_id[:12],
                    "name": "unknown",
                    "status": "unknown",
                    "image": "unknown"
                })
        
        return {"containers": containers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/docker/containers/{container_id}/execute")
async def execute_command(container_id: str, command: str):
    """Execute a command in a container"""
    if not docker_server:
        raise HTTPException(status_code=500, detail="Docker server not initialized")
    
    try:
        container = docker_server._find_container(container_id)
        if not container:
            raise HTTPException(status_code=404, detail=f"Container {container_id} not found")
        
        result = container.exec_run(command)
        output = f"Exit code: {result.exit_code}\nOutput:\n{result.output.decode('utf-8')}"
        
        operation = DockerOperation(
            operation="execute_command",
            parameters={"container_id": container_id, "command": command},
            result=output
        )
        operation_logs.append(operation)
        
        return {"result": output}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/docker/images")
async def list_allowed_images():
    """Get list of allowed Docker images"""
    if not docker_server:
        raise HTTPException(status_code=500, detail="Docker server not initialized")
    
    return {"images": sorted(list(docker_server.allowed_images))}

@app.get("/api/docker/gpu-status")
async def get_gpu_status():
    """Get NVIDIA GPU status"""
    if not docker_server:
        raise HTTPException(status_code=500, detail="Docker server not initialized")
    
    return {
        "gpu_available": docker_server.gpu_available,
        "status": await get_gpu_info() if docker_server.gpu_available else "GPU not available"
    }

async def get_gpu_info():
    """Helper function to get GPU information"""
    try:
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
                    gpu_info.append({
                        "id": i,
                        "name": name,
                        "memory_total": total_mem,
                        "memory_used": used_mem,
                        "utilization": util
                    })
            return gpu_info
        else:
            return f"nvidia-smi error: {result.stderr}"
    except Exception as e:
        return f"Error getting GPU info: {str(e)}"

# Docker Scout Security APIs
@app.post("/api/docker/scout/scan/{image}")
async def scout_scan_vulnerabilities(image: str):
    """Scan image for vulnerabilities using Docker Scout"""
    if not docker_server:
        raise HTTPException(status_code=500, detail="Docker server not initialized")
    
    if image not in docker_server.allowed_images:
        raise HTTPException(status_code=400, detail=f"Image '{image}' not allowed")
    
    result = docker_server._run_docker_scout_command(["cves", image])
    return {"result": result}

@app.post("/api/docker/scout/recommendations/{image}")
async def scout_get_recommendations(image: str):
    """Get security recommendations for an image"""
    if not docker_server:
        raise HTTPException(status_code=500, detail="Docker server not initialized")
    
    if image not in docker_server.allowed_images:
        raise HTTPException(status_code=400, detail=f"Image '{image}' not allowed")
    
    result = docker_server._run_docker_scout_command(["recommendations", image])
    return {"result": result}

# AI Chat API
@app.post("/api/chat")
async def chat_with_ai(provider_name: str, message: str, include_docker_context: bool = False):
    """Send a message to an AI provider with optional Docker context"""
    if provider_name not in ai_providers:
        raise HTTPException(status_code=404, detail="AI provider not found")
    
    provider = ai_providers[provider_name]
    
    # Build context if requested
    context = ""
    if include_docker_context:
        context = f"""
Available Docker operations:
- Images: {', '.join(docker_server.allowed_images if docker_server else [])}
- Active containers: {len(docker_server.active_containers) if docker_server else 0}
- Recent operations: {len(operation_logs)}

You can help manage Docker containers, scan for vulnerabilities, and execute commands.
"""
    
    # Add message to history
    user_message = ChatMessage(role="user", content=message, timestamp=datetime.now())
    chat_history.append(user_message)
    
    try:
        # Make API call to AI provider
        async with httpx.AsyncClient() as client:
            if "openai" in provider.base_url.lower():
                # OpenAI API format
                response = await client.post(
                    f"{provider.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {provider.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": provider.model,
                        "messages": [
                            {"role": "system", "content": f"You are an AI assistant helping with Docker operations.{context}"},
                            {"role": "user", "content": message}
                        ]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_content = data["choices"][0]["message"]["content"]
                else:
                    ai_content = f"Error: {response.status_code} - {response.text}"
                    
            elif "anthropic" in provider.base_url.lower():
                # Anthropic API format
                response = await client.post(
                    f"{provider.base_url}/messages",
                    headers={
                        "x-api-key": provider.api_key,
                        "Content-Type": "application/json",
                        "anthropic-version": "2023-06-01"
                    },
                    json={
                        "model": provider.model,
                        "max_tokens": 1024,
                        "messages": [{"role": "user", "content": f"{context}\n\n{message}"}]
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    ai_content = data["content"][0]["text"]
                else:
                    ai_content = f"Error: {response.status_code} - {response.text}"
            else:
                # Generic API format
                ai_content = "Generic AI provider integration not yet implemented"
        
        # Add AI response to history
        ai_message = ChatMessage(role="assistant", content=ai_content, timestamp=datetime.now())
        chat_history.append(ai_message)
        
        return AIResponse(success=True, content=ai_content)
        
    except Exception as e:
        error_msg = f"Error communicating with AI: {str(e)}"
        return AIResponse(success=False, content="", error=error_msg)

@app.get("/api/chat/history")
async def get_chat_history():
    """Get chat history"""
    return {"messages": chat_history}

@app.delete("/api/chat/history")
async def clear_chat_history():
    """Clear chat history"""
    chat_history.clear()
    return {"message": "Chat history cleared"}

# Main UI Route
@app.get("/", response_class=HTMLResponse)
async def main_ui(request: Request):
    """Main web interface"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "providers": ai_providers,
        "containers": len(docker_server.active_containers) if docker_server else 0
    })

# API Documentation
@app.get("/api/operations")
async def get_operation_logs():
    """Get Docker operation logs"""
    return {"operations": operation_logs}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)