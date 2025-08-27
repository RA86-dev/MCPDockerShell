"""
Development tools for coding, project scaffolding, and AI-assisted development
"""
import json
import os
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from notify import ntfyClient

class DevelopmentTools:
    """Development and coding assistance tools"""
    
    def __init__(self, docker_client, active_containers: dict, temp_dir: str, logger=None,baseurl=""):
        self.docker_client = docker_client
        self.active_containers = active_containers
        self.temp_dir = Path(temp_dir)
        self.logger = logger
        self.ntfy_client = ntfyClient(
            base_url=baseurl
        )
        
    def register_tools(self, mcp_server):
        """Register development tools with the MCP server"""
        
        @mcp_server.tool()
        async def create_dev_environment(language: str, project_name: str, features: List[str] = None) -> str:
            self.ntfy_client.send_message(
                ""
            )
            """Create a development environment with pre-configured tools"""
            try:
                # Language-specific base images
                language_configs = {
                    "python": {
                        "image": "python:3.11-slim",
                        "packages": ["python3-pip", "git", "curl", "vim", "build-essential"],
                        "setup_commands": [
                            "pip install --upgrade pip",
                            "pip install pytest black flake8 mypy"
                        ]
                    },
                    "node": {
                        "image": "node:18-alpine",
                        "packages": ["git", "curl", "vim"],
                        "setup_commands": [
                            "npm install -g nodemon jest eslint prettier"
                        ]
                    },
                    "java": {
                        "image": "openjdk:17-slim",
                        "packages": ["git", "curl", "vim", "maven"],
                        "setup_commands": []
                    },
                    "golang": {
                        "image": "golang:1.21-alpine",
                        "packages": ["git", "curl", "vim"],
                        "setup_commands": []
                    },
                    "rust": {
                        "image": "rust:latest",
                        "packages": ["git", "curl", "vim", "build-essential"],
                        "setup_commands": []
                    }
                }
                
                if language not in language_configs:
                    return f"Unsupported language: {language}. Supported: {', '.join(language_configs.keys())}"
                
                config = language_configs[language]
                container_name = f"dev_{language}_{project_name}_{int(time.time())}"
                
                # Create container
                container = self.docker_client.containers.run(
                    image=config["image"],
                    name=container_name,
                    detach=True,
                    stdin_open=True,
                    tty=True,
                    working_dir="/workspace",
                    volumes={"/tmp/workspace": {"bind": "/workspace", "mode": "rw"}},
                    command="/bin/bash" if "alpine" not in config["image"] else "/bin/sh"
                )
                
                # Store container info
                self.active_containers[container.id] = {
                    "container": container,
                    "name": container_name,
                    "created_at": time.time(),
                    "image": config["image"]
                }
                
                # Install packages and run setup commands
                if config["packages"]:
                    if "alpine" in config["image"]:
                        install_cmd = f"apk add --no-cache {' '.join(config['packages'])}"
                    else:
                        install_cmd = f"apt-get update && apt-get install -y {' '.join(config['packages'])}"
                    
                    container.exec_run(install_cmd)
                
                for cmd in config["setup_commands"]:
                    container.exec_run(cmd)
                
                # Create project structure
                project_dir = f"/workspace/{project_name}"
                container.exec_run(f"mkdir -p {project_dir}")
                
                return f"Development environment created: {container_name} ({container.id[:12]})"
                
            except Exception as e:
                return f"Error creating development environment: {str(e)}"

        @mcp_server.tool()
        async def generate_project_template(
            language: str, 
            project_name: str, 
            features: List[str] = None
        ) -> str:
            """Generate a project template with common structure and files"""
            try:
                project_path = Path("/tmp/workspace") / project_name
                project_path.mkdir(parents=True, exist_ok=True)
                
                features = features or []
                
                if language == "python":
                    # Create Python project structure
                    (project_path / "src").mkdir(exist_ok=True)
                    (project_path / "tests").mkdir(exist_ok=True)
                    (project_path / "docs").mkdir(exist_ok=True)
                    
                    # requirements.txt
                    requirements = ["requests>=2.31.0"]
                    if "testing" in features:
                        requirements.extend(["pytest>=7.4.0", "pytest-cov>=4.1.0"])
                    if "linting" in features:
                        requirements.extend(["black>=23.0.0", "flake8>=6.0.0", "mypy>=1.5.0"])
                    if "fastapi" in features:
                        requirements.extend(["fastapi>=0.104.0", "uvicorn>=0.24.0"])
                    if "django" in features:
                        requirements.append("Django>=4.2.0")
                    
                    with open(project_path / "requirements.txt", "w") as f:
                        f.write("\n".join(requirements))
                    
                    # main.py
                    main_content = f'"""\n{project_name} - Main application\n"""\n\ndef main():\n    print("Hello from {project_name}!")\n\nif __name__ == "__main__":\n    main()\n'
                    with open(project_path / "src" / "main.py", "w") as f:
                        f.write(main_content)
                    
                    # setup.py
                    setup_content = f"""from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="0.1.0",
    description="{project_name} application",
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    python_requires=">=3.8",
    install_requires=open("requirements.txt").read().splitlines(),
)"""
                    with open(project_path / "setup.py", "w") as f:
                        f.write(setup_content)
                
                elif language == "node":
                    # Create Node.js project structure
                    (project_path / "src").mkdir(exist_ok=True)
                    (project_path / "tests").mkdir(exist_ok=True)
                    
                    # package.json
                    dependencies = {"express": "^4.18.0"}
                    dev_dependencies = {"nodemon": "^3.0.0", "jest": "^29.5.0"}
                    
                    if "typescript" in features:
                        dependencies["typescript"] = "^5.2.0"
                        dev_dependencies["@types/node"] = "^20.0.0"
                        dev_dependencies["ts-node"] = "^10.9.0"
                    
                    package_json = {
                        "name": project_name.lower().replace(" ", "-"),
                        "version": "1.0.0",
                        "description": f"{project_name} application",
                        "main": "src/index.js",
                        "scripts": {
                            "start": "node src/index.js",
                            "dev": "nodemon src/index.js",
                            "test": "jest",
                        },
                        "dependencies": dependencies,
                        "devDependencies": dev_dependencies,
                    }
                    
                    with open(project_path / "package.json", "w") as f:
                        f.write(json.dumps(package_json, indent=2))
                    
                    # index.js
                    with open(project_path / "src" / "index.js", "w") as f:
                        f.write(f"""const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {{
    res.json({{ message: 'Hello from {project_name}!' }});
}});

app.listen(PORT, () => {{
    console.log(`{project_name} server running on port ${{PORT}}`);
}});

module.exports = app;
""")
                
                elif language == "java":
                    # Create Java project structure
                    java_package_path = project_path / "src" / "main" / "java" / "com" / "example" / project_name.lower()
                    java_package_path.mkdir(parents=True, exist_ok=True)
                    
                    test_package_path = project_path / "src" / "test" / "java" / "com" / "example" / project_name.lower()
                    test_package_path.mkdir(parents=True, exist_ok=True)
                    
                    # pom.xml for Maven
                    pom_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.example</groupId>
    <artifactId>{project_name.lower()}</artifactId>
    <version>1.0.0</version>
    
    <properties>
        <maven.compiler.source>17</maven.compiler.source>
        <maven.compiler.target>17</maven.compiler.target>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
            <scope>test</scope>
        </dependency>
    </dependencies>
</project>"""
                    
                    with open(project_path / "pom.xml", "w") as f:
                        f.write(pom_content)
                    
                    # Main.java
                    main_java = f"""package com.example.{project_name.lower()};

public class Main {{
    public static void main(String[] args) {{
        System.out.println("Hello from {project_name}!");
    }}
}}"""
                    
                    with open(java_package_path / "Main.java", "w") as f:
                        f.write(main_java)
                
                # Create common files for all languages
                with open(project_path / "README.md", "w") as f:
                    f.write(f"""# {project_name}

## Description
{project_name} application built with {language}

## Features
{chr(10).join(f"- {feature}" for feature in features) if features else "- Basic application structure"}

## Installation
```bash
# Install dependencies
{"pip install -r requirements.txt" if language == "python" else "npm install" if language == "node" else "mvn install" if language == "java" else "cargo build" if language == "rust" else "go mod tidy"}
```

## Usage
```bash
# Run the application
{"python src/main.py" if language == "python" else "npm start" if language == "node" else "mvn exec:java" if language == "java" else "cargo run" if language == "rust" else "go run ."}
```

## Development
```bash
# Run tests
{"pytest" if language == "python" else "npm test" if language == "node" else "mvn test" if language == "java" else "cargo test" if language == "rust" else "go test"}
```
""")
                
                # .gitignore
                gitignore_content = {
                    "python": "__pycache__/\n*.pyc\n*.pyo\n*.pyd\n.env\n.venv/\ndist/\nbuild/\n*.egg-info/",
                    "node": "node_modules/\nnpm-debug.log*\n.env\ndist/\nbuild/",
                    "java": "target/\n*.class\n*.jar\n*.war\n*.ear",
                    "golang": "bin/\n*.exe\ngo.sum",
                    "rust": "target/\nCargo.lock"
                }.get(language, "")
                
                with open(project_path / ".gitignore", "w") as f:
                    f.write(gitignore_content)
                
                return f"Project template created for {project_name} ({language}) with features: {', '.join(features) if features else 'basic'}"
                
            except Exception as e:
                return f"Error generating project template: {str(e)}"

        @mcp_server.tool()
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
                
                file_content = result.output.decode('utf-8')
                
                # Basic code analysis
                analysis = {
                    "file_path": file_path,
                    "lines_of_code": len(file_content.splitlines()),
                    "file_size_bytes": len(file_content.encode('utf-8')),
                    "suggestions": []
                }
                
                # Language detection and basic analysis
                file_ext = Path(file_path).suffix.lower()
                
                if file_ext == '.py':
                    analysis["language"] = "Python"
                    # Check for common Python issues
                    lines = file_content.splitlines()
                    for i, line in enumerate(lines, 1):
                        if line.strip().startswith('print(') and '"' in line:
                            analysis["suggestions"].append({
                                "line": i,
                                "type": "style",
                                "message": "Consider using logging instead of print for production code"
                            })
                        if 'import *' in line:
                            analysis["suggestions"].append({
                                "line": i,
                                "type": "best_practice",
                                "message": "Avoid wildcard imports, import specific modules"
                            })
                
                elif file_ext == '.js':
                    analysis["language"] = "JavaScript"
                    # Check for common JavaScript issues
                    if 'var ' in file_content:
                        analysis["suggestions"].append({
                            "type": "modernization",
                            "message": "Consider using 'let' or 'const' instead of 'var'"
                        })
                
                elif file_ext == '.java':
                    analysis["language"] = "Java"
                    if 'System.out.println' in file_content:
                        analysis["suggestions"].append({
                            "type": "best_practice",
                            "message": "Consider using a logging framework instead of System.out.println"
                        })
                
                return json.dumps(analysis, indent=2)
                
            except Exception as e:
                return f"Error analyzing code: {str(e)}"

    def _find_container(self, container_id: str):
        """Find a container by ID or name"""
        try:
            # Try exact match first
            if container_id in self.active_containers:
                return self.active_containers[container_id]["container"]
            
            # Try to get from Docker directly
            try:
                return self.docker_client.containers.get(container_id)
            except Exception:
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