"""
Workflow automation and CI/CD tools
"""
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from subtools.notify import ntfyClient

class WorkflowTools:
    """Workflow automation and CI/CD functionality"""
    
    def __init__(self, temp_dir: str, logger=None):
        self.temp_dir = Path(temp_dir)
        self.logger = logger
        
    def register_tools(self, mcp_server):
        """Register workflow automation tools with the MCP server"""
        
        @mcp_server.tool()
        async def create_dockerfile(language: str, project_name: str) -> str:
            """Generate a Dockerfile template for the specified language"""
            try:
                dockerfile_templates = {
                    "python": f"""FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "app.py"]
""",
                    "node": f"""FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

EXPOSE 3000

CMD ["npm", "start"]
""",
                    "golang": f"""FROM golang:1.21-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

FROM alpine:latest
RUN apk --no-cache add ca-certificates
WORKDIR /root/

COPY --from=builder /app/main .

EXPOSE 8080

CMD ["./main"]
""",
                    "java": f"""FROM openjdk:17-jre-slim

WORKDIR /app

COPY target/{project_name}-*.jar app.jar

EXPOSE 8080

CMD ["java", "-jar", "app.jar"]
""",
                    "rust": f"""FROM rust:1.70 AS builder

WORKDIR /app
COPY Cargo.toml Cargo.lock ./
COPY src ./src

RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/target/release/{project_name} /usr/local/bin/app

EXPOSE 8000

CMD ["app"]
"""
                }
                
                if language not in dockerfile_templates:
                    return f"Unsupported language: {language}. Supported: {', '.join(dockerfile_templates.keys())}"
                
                dockerfile_content = dockerfile_templates[language]
                
                # Save to workspace
                workspace_path = Path("/tmp/workspace") / project_name
                workspace_path.mkdir(parents=True, exist_ok=True)
                
                dockerfile_path = workspace_path / "Dockerfile"
                with open(dockerfile_path, "w") as f:
                    f.write(dockerfile_content)
                
                return f"Dockerfile created for {language} project: {dockerfile_path}"
                
            except Exception as e:
                return f"Error creating Dockerfile: {str(e)}"

        @mcp_server.tool()
        async def create_docker_compose(
            services: List[Dict[str, Any]], 
            project_name: str,
            include_volumes: bool = True,
            include_networks: bool = True
        ) -> str:
            """Generate a docker-compose.yml file for multi-service applications"""
            try:
                compose_data = {
                    "version": "3.8",
                    "services": {}
                }
                
                for service in services:
                    service_name = service.get("name", "app")
                    compose_data["services"][service_name] = {
                        "build": service.get("build", "."),
                        "ports": service.get("ports", []),
                        "environment": service.get("environment", {}),
                        "volumes": service.get("volumes", []),
                        "depends_on": service.get("depends_on", [])
                    }
                    
                    if service.get("image"):
                        compose_data["services"][service_name]["image"] = service["image"]
                        del compose_data["services"][service_name]["build"]
                
                if include_volumes:
                    compose_data["volumes"] = {
                        f"{project_name}_data": {}
                    }
                
                if include_networks:
                    compose_data["networks"] = {
                        f"{project_name}_network": {
                            "driver": "bridge"
                        }
                    }
                
                # Save to workspace
                workspace_path = Path("/tmp/workspace") / project_name
                workspace_path.mkdir(parents=True, exist_ok=True)
                
                compose_path = workspace_path / "docker-compose.yml"
                with open(compose_path, "w") as f:
                    import yaml
                    yaml.dump(compose_data, f, default_flow_style=False, indent=2)
                
                return f"Docker Compose file created: {compose_path}"
                
            except Exception as e:
                return f"Error creating Docker Compose file: {str(e)}"

        @mcp_server.tool()
        async def create_github_workflow(
            language: str, 
            project_name: str,
            include_tests: bool = True,
            include_docker: bool = False,
            deploy_target: str = None
        ) -> str:
            """Generate GitHub Actions workflow file"""
            try:
                workflow_templates = {
                    "python": {
                        "name": f"CI/CD for {project_name}",
                        "on": {
                            "push": {"branches": ["main", "develop"]},
                            "pull_request": {"branches": ["main"]}
                        },
                        "jobs": {
                            "test": {
                                "runs-on": "ubuntu-latest",
                                "steps": [
                                    {"uses": "actions/checkout@v3"},
                                    {
                                        "name": "Set up Python",
                                        "uses": "actions/setup-python@v4",
                                        "with": {"python-version": "3.11"}
                                    },
                                    {
                                        "name": "Install dependencies",
                                        "run": "pip install -r requirements.txt"
                                    }
                                ]
                            }
                        }
                    },
                    "node": {
                        "name": f"CI/CD for {project_name}",
                        "on": {
                            "push": {"branches": ["main", "develop"]},
                            "pull_request": {"branches": ["main"]}
                        },
                        "jobs": {
                            "test": {
                                "runs-on": "ubuntu-latest",
                                "steps": [
                                    {"uses": "actions/checkout@v3"},
                                    {
                                        "name": "Setup Node.js",
                                        "uses": "actions/setup-node@v3",
                                        "with": {"node-version": "18"}
                                    },
                                    {"name": "Install dependencies", "run": "npm ci"}
                                ]
                            }
                        }
                    }
                }
                
                if language not in workflow_templates:
                    return f"Unsupported language: {language}. Supported: {', '.join(workflow_templates.keys())}"
                
                workflow_data = workflow_templates[language]
                
                # Add test step if requested
                if include_tests:
                    if language == "python":
                        workflow_data["jobs"]["test"]["steps"].append({
                            "name": "Run tests",
                            "run": "pytest --cov=src tests/"
                        })
                    elif language == "node":
                        workflow_data["jobs"]["test"]["steps"].append({
                            "name": "Run tests",
                            "run": "npm test"
                        })
                
                # Add Docker build step if requested
                if include_docker:
                    docker_job = {
                        "build-and-push": {
                            "runs-on": "ubuntu-latest",
                            "needs": "test",
                            "if": "github.ref == 'refs/heads/main'",
                            "steps": [
                                {"uses": "actions/checkout@v3"},
                                {
                                    "name": "Build Docker image",
                                    "run": f"docker build -t {project_name}:latest ."
                                }
                            ]
                        }
                    }
                    workflow_data["jobs"].update(docker_job)
                
                # Save to workspace
                workspace_path = Path("/tmp/workspace") / project_name / ".github" / "workflows"
                workspace_path.mkdir(parents=True, exist_ok=True)
                
                workflow_path = workspace_path / "ci.yml"
                with open(workflow_path, "w") as f:
                    import yaml
                    yaml.dump(workflow_data, f, default_flow_style=False, indent=2)
                
                return f"GitHub Actions workflow created: {workflow_path}"
                
            except Exception as e:
                return f"Error creating GitHub workflow: {str(e)}"

        @mcp_server.tool()
        async def setup_ci_cd_pipeline(
            project_name: str,
            language: str,
            platform: str = "github",
            include_testing: bool = True,
            include_deployment: bool = False
        ) -> str:
            """Setup a complete CI/CD pipeline with all necessary files"""
            try:
                project_path = Path("/tmp/workspace") / project_name
                project_path.mkdir(parents=True, exist_ok=True)
                
                files_created = []
                
                # Create Dockerfile
                dockerfile_result = await create_dockerfile(language, project_name)
                files_created.append("Dockerfile")
                
                # Create basic docker-compose for development
                if language == "python":
                    services = [{
                        "name": "web",
                        "build": ".",
                        "ports": ["8000:8000"],
                        "environment": {"DEBUG": "1"},
                        "volumes": [".:/app"]
                    }]
                elif language == "node":
                    services = [{
                        "name": "web", 
                        "build": ".",
                        "ports": ["3000:3000"],
                        "environment": {"NODE_ENV": "development"},
                        "volumes": [".:/app"]
                    }]
                else:
                    services = [{"name": "web", "build": ".", "ports": ["8080:8080"]}]
                
                # Add database service if needed
                if include_deployment:
                    services.extend([
                        {
                            "name": "db",
                            "image": "postgres:15",
                            "environment": {
                                "POSTGRES_DB": project_name,
                                "POSTGRES_USER": "user",
                                "POSTGRES_PASSWORD": "password"
                            },
                            "ports": ["5432:5432"],
                            "volumes": [f"{project_name}_postgres_data:/var/lib/postgresql/data"]
                        },
                        {
                            "name": "redis",
                            "image": "redis:7-alpine",
                            "ports": ["6379:6379"]
                        }
                    ])
                
                compose_result = await create_docker_compose(services, project_name)
                files_created.append("docker-compose.yml")
                
                # Create CI/CD workflow
                if platform == "github":
                    workflow_result = await create_github_workflow(
                        language, 
                        project_name, 
                        include_testing, 
                        True,  # include docker
                        "docker" if include_deployment else None
                    )
                    files_created.append(".github/workflows/ci.yml")
                
                # Create environment-specific docker-compose files
                docker_compose_prod = f"""version: '3.8'
services:
  web:
    build: .
    ports:
      - "80:8000"
    environment:
      - NODE_ENV=production
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: {project_name}
      POSTGRES_USER: ${{POSTGRES_USER}}
      POSTGRES_PASSWORD: ${{POSTGRES_PASSWORD}}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    ports:
      - "6379:6379"

volumes:
  postgres_data:
"""
                
                with open(project_path / "docker-compose.prod.yml", "w") as f:
                    f.write(docker_compose_prod)
                files_created.append("docker-compose.prod.yml")
                
                return f"CI/CD pipeline configured for {project_name} ({language}) on {platform}. Files created: {', '.join(files_created)}"
                
            except Exception as e:
                return f"Error setting up CI/CD pipeline: {str(e)}"

        @mcp_server.tool()
        async def create_makefile(project_name: str, language: str) -> str:
            """Generate a Makefile for common project tasks"""
            try:
                makefile_templates = {
                    "python": f"""# Makefile for {project_name}

.PHONY: install test lint format clean build docker-build docker-run

install:
\tpip install -r requirements.txt

test:
\tpytest tests/ -v --cov=src

lint:
\tflake8 src tests
\tmypy src

format:
\tblack src tests
\tisort src tests

clean:
\tfind . -type f -name "*.pyc" -delete
\tfind . -type d -name "__pycache__" -delete
\trm -rf .pytest_cache
\trm -rf .coverage
\trm -rf dist/
\trm -rf build/

build:
\tpython setup.py sdist bdist_wheel

docker-build:
\tdocker build -t {project_name}:latest .

docker-run:
\tdocker run -p 8000:8000 {project_name}:latest

dev:
\tpython src/main.py

deploy:
\tdocker-compose -f docker-compose.prod.yml up -d
""",
                    "node": f"""# Makefile for {project_name}

.PHONY: install test lint format clean build docker-build docker-run

install:
\tnpm install

test:
\tnpm test

lint:
\tnpm run lint

format:
\tnpm run format

clean:
\trm -rf node_modules
\trm -rf dist/
\trm -rf build/

build:
\tnpm run build

docker-build:
\tdocker build -t {project_name}:latest .

docker-run:
\tdocker run -p 3000:3000 {project_name}:latest

dev:
\tnpm run dev

deploy:
\tdocker-compose -f docker-compose.prod.yml up -d
"""
                }
                
                if language not in makefile_templates:
                    return f"Unsupported language: {language}. Supported: {', '.join(makefile_templates.keys())}"
                
                makefile_content = makefile_templates[language]
                
                # Save to workspace
                workspace_path = Path("/tmp/workspace") / project_name
                workspace_path.mkdir(parents=True, exist_ok=True)
                
                makefile_path = workspace_path / "Makefile"
                with open(makefile_path, "w") as f:
                    f.write(makefile_content)
                
                return f"Makefile created for {language} project: {makefile_path}"
                
            except Exception as e:
                return f"Error creating Makefile: {str(e)}"