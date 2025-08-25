# Usage Examples

This guide provides comprehensive examples of how to use the MCP Docker Developer Server for various development tasks and workflows.

## Getting Started Examples

### Basic Container Operations

#### Example 1: Creating a Python Development Environment

```python
# Create a Python container for development
container = await create_container(
    image="python:3.11-slim",
    name="python-dev-env",
    environment={"PYTHONPATH": "/workspace"},
    ports={"5000": 8080}  # Map container port 5000 to host port 8080
)

# Create a simple Python script
await create_file_in_container(
    container_id=container.id,
    file_path="/workspace/hello.py",
    content="""
def greet(name):
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("Docker World"))
"""
)

# Execute the Python script
result = await execute_command(
    container_id=container.id,
    command="python /workspace/hello.py"
)

print(f"Output: {result.stdout}")
# Output: Hello, Docker World!
```

#### Example 2: Node.js Application Development

```python
# Create Node.js development container
node_container = await create_container(
    image="node:18-alpine",
    name="node-app-dev",
    environment={"NODE_ENV": "development"},
    ports={"3000": 3000}
)

# Create a package.json file
package_json = {
    "name": "demo-app",
    "version": "1.0.0", 
    "scripts": {
        "start": "node server.js",
        "dev": "node --watch server.js"
    },
    "dependencies": {
        "express": "^4.18.0"
    }
}

await create_file_in_container(
    container_id=node_container.id,
    file_path="/workspace/package.json",
    content=json.dumps(package_json, indent=2)
)

# Create a simple Express server
server_code = """
const express = require('express');
const app = express();
const PORT = 3000;

app.get('/', (req, res) => {
    res.json({ message: 'Hello from Docker container!', timestamp: new Date() });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on port ${PORT}`);
});
"""

await create_file_in_container(
    container_id=node_container.id,
    file_path="/workspace/server.js",
    content=server_code
)

# Install dependencies and start the server
await execute_command(
    container_id=node_container.id,
    command="cd /workspace && npm install"
)

await execute_command(
    container_id=node_container.id,
    command="cd /workspace && npm start &"
)
```

## Documentation and Research Examples

### Example 3: Multi-Language Documentation Research

```python
# Research async programming across multiple languages
languages_to_research = ["python", "javascript", "java", "go"]
research_results = {}

for language in languages_to_research:
    # Search for async programming documentation
    docs = await search_language_docs(
        language=language,
        query="async await concurrency",
        max_results=3
    )
    
    research_results[language] = docs
    
    # Get detailed documentation for the first result
    if docs:
        detailed_doc = await read_language_doc(
            language=language,
            file_path=docs[0]['file_path'],
            max_lines=100
        )
        research_results[f"{language}_detailed"] = detailed_doc

# Compare async patterns across languages
for language, docs in research_results.items():
    if not language.endswith("_detailed"):
        print(f"\n{language.upper()} Async Resources:")
        for doc in docs[:2]:  # Show top 2 results
            print(f"  - {doc['title']}: {doc['summary']}")
```

### Example 4: Framework Comparison Research

```python
# Compare React vs Vue.js component patterns
frameworks = [
    {"name": "react", "query": "component lifecycle hooks"},
    {"name": "vue", "query": "component lifecycle hooks"}
]

comparison_data = {}

for framework in frameworks:
    results = await search_language_docs(
        language=framework["name"],
        query=framework["query"],
        max_results=5
    )
    
    comparison_data[framework["name"]] = {
        "lifecycle_concepts": results,
        "component_examples": await search_language_docs(
            language=framework["name"],
            query="component example tutorial",
            max_results=3
        )
    }

# Generate comparison report
print("Framework Comparison: React vs Vue.js")
print("="*50)
for framework_name, data in comparison_data.items():
    print(f"\n{framework_name.upper()} Component Lifecycle:")
    for concept in data["lifecycle_concepts"][:3]:
        print(f"  • {concept['title']}")
```

## Web Automation Examples

### Example 5: Automated Testing with Playwright

```python
# Create a comprehensive web testing workflow
async def test_web_application():
    # Launch browser
    browser = await playwright_launch_browser(
        browser_type="chromium",
        headless=False  # Show browser for demo
    )
    
    # Create new page
    page = await playwright_create_page(
        browser_id=browser.id,
        viewport_width=1280,
        viewport_height=800
    )
    
    # Navigate to the application
    await playwright_navigate(
        page_id=page.id,
        url="https://example.com",
        wait_until="networkidle"
    )
    
    # Take screenshot of initial state
    await playwright_screenshot(
        page_id=page.id,
        filename="initial_load.png",
        full_page=True
    )
    
    # Test form interaction
    await playwright_click(page_id=page.id, selector="#contact-form")
    await playwright_type(page_id=page.id, selector="#name", text="Test User")
    await playwright_type(page_id=page.id, selector="#email", text="test@example.com")
    
    # Submit form
    await playwright_click(page_id=page.id, selector="#submit-btn")
    
    # Wait for success message
    await playwright_wait_for_selector(
        page_id=page.id,
        selector=".success-message",
        timeout=10000
    )
    
    # Capture success screenshot
    await playwright_screenshot(
        page_id=page.id,
        filename="form_success.png"
    )
    
    # Get confirmation text
    confirmation = await playwright_get_text(
        page_id=page.id,
        selector=".success-message"
    )
    
    # Cleanup
    await playwright_close_page(page_id=page.id)
    await playwright_close_browser(browser_id=browser.id)
    
    return confirmation

# Run the test
result = await test_web_application()
print(f"Test completed with message: {result}")
```

### Example 6: Cross-Browser Compatibility Testing

```python
# Test across multiple browsers
browsers = ["chromium", "firefox", "webkit"]
test_results = {}

for browser_type in browsers:
    try:
        # Launch browser
        browser = await playwright_launch_browser(
            browser_type=browser_type,
            headless=True
        )
        
        page = await playwright_create_page(browser_id=browser.id)
        
        # Navigate to test page
        await playwright_navigate(
            page_id=page.id,
            url="https://caniuse.com"
        )
        
        # Test CSS Grid support detection
        grid_support = await playwright_evaluate(
            page_id=page.id,
            script="""
            () => {
                const testElement = document.createElement('div');
                testElement.style.display = 'grid';
                return testElement.style.display === 'grid';
            }
            """
        )
        
        # Test modern JavaScript features
        js_support = await playwright_evaluate(
            page_id=page.id,
            script="""
            () => {
                try {
                    // Test async/await
                    eval('(async () => {})');
                    // Test destructuring
                    eval('const {a} = {a: 1}');
                    // Test arrow functions
                    eval('() => {}');
                    return true;
                } catch (e) {
                    return false;
                }
            }
            """
        )
        
        test_results[browser_type] = {
            "css_grid": grid_support,
            "modern_js": js_support,
            "status": "passed"
        }
        
        await playwright_close_page(page_id=page.id)
        await playwright_close_browser(browser_id=browser.id)
        
    except Exception as e:
        test_results[browser_type] = {
            "error": str(e),
            "status": "failed"
        }

# Generate compatibility report
print("Cross-Browser Compatibility Report")
print("="*40)
for browser, results in test_results.items():
    print(f"\n{browser.upper()}:")
    if results["status"] == "passed":
        print(f"  ✓ CSS Grid Support: {results['css_grid']}")
        print(f"  ✓ Modern JS Support: {results['modern_js']}")
    else:
        print(f"  ✗ Error: {results['error']}")
```

## Development Workflow Examples

### Example 7: Complete Python Project Workflow

```python
async def python_development_workflow():
    # Create Python development container
    container = await create_container(
        image="python:3.11-slim",
        name="python-project-dev",
        environment={
            "PYTHONPATH": "/workspace",
            "FLASK_APP": "app.py",
            "FLASK_ENV": "development"
        },
        ports={"5000": 5000}
    )
    
    # Create project structure
    project_files = {
        "/workspace/requirements.txt": """
flask==2.3.0
pytest==7.4.0
black==23.0.0
pylint==2.17.0
""",
        "/workspace/app.py": """
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return jsonify({"message": "Hello, World!", "status": "success"})

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
""",
        "/workspace/test_app.py": """
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_hello(client):
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Hello, World!'
    assert data['status'] == 'success'

def test_health(client):
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
""",
        "/workspace/.pylintrc": """
[MASTER]
disable=C0114,C0115,C0116
"""
    }
    
    # Create all project files
    for file_path, content in project_files.items():
        await create_file_in_container(
            container_id=container.id,
            file_path=file_path,
            content=content.strip()
        )
    
    # Install dependencies
    install_result = await execute_command(
        container_id=container.id,
        command="cd /workspace && pip install -r requirements.txt"
    )
    print("Dependencies installed:", install_result.success)
    
    # Run code formatting
    format_result = await execute_command(
        container_id=container.id,
        command="cd /workspace && black *.py"
    )
    print("Code formatted:", format_result.success)
    
    # Run linting
    lint_result = await execute_command(
        container_id=container.id,
        command="cd /workspace && pylint app.py"
    )
    print("Linting completed")
    
    # Run tests
    test_result = await execute_command(
        container_id=container.id,
        command="cd /workspace && python -m pytest test_app.py -v"
    )
    print("Tests executed:", test_result.success)
    
    # Start the application
    app_result = await stream_command_execution(
        container_id=container.id,
        command="cd /workspace && python app.py"
    )
    
    return {
        "container_id": container.id,
        "setup_successful": all([
            install_result.success,
            format_result.success,
            test_result.success
        ]),
        "app_stream": app_result
    }

# Execute the workflow
workflow_result = await python_development_workflow()
print(f"Development workflow completed: {workflow_result['setup_successful']}")
```

### Example 8: Full-Stack Application Development

```python
async def fullstack_development():
    # Backend container (Node.js API)
    backend_container = await create_container(
        image="node:18-alpine",
        name="backend-api",
        environment={"NODE_ENV": "development"},
        ports={"3001": 3001}
    )
    
    # Frontend container (React app)
    frontend_container = await create_container(
        image="node:18-alpine",
        name="frontend-app",
        environment={"NODE_ENV": "development"},
        ports={"3000": 3000}
    )
    
    # Database container (for completeness)
    db_container = await create_container(
        image="postgres:15-alpine",
        name="app-database",
        environment={
            "POSTGRES_DB": "appdb",
            "POSTGRES_USER": "appuser",
            "POSTGRES_PASSWORD": "password"
        },
        ports={"5432": 5432}
    )
    
    # Backend API setup
    backend_package_json = {
        "name": "backend-api",
        "version": "1.0.0",
        "scripts": {
            "start": "node server.js",
            "dev": "node --watch server.js"
        },
        "dependencies": {
            "express": "^4.18.0",
            "cors": "^2.8.5",
            "pg": "^8.8.0"
        }
    }
    
    await create_file_in_container(
        container_id=backend_container.id,
        file_path="/workspace/package.json",
        content=json.dumps(backend_package_json, indent=2)
    )
    
    # Backend server code
    backend_server = """
const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 3001;

app.use(cors());
app.use(express.json());

// API routes
app.get('/api/health', (req, res) => {
    res.json({ status: 'healthy', timestamp: new Date() });
});

app.get('/api/users', (req, res) => {
    // Mock users data
    const users = [
        { id: 1, name: 'John Doe', email: 'john@example.com' },
        { id: 2, name: 'Jane Smith', email: 'jane@example.com' }
    ];
    res.json({ users });
});

app.listen(PORT, '0.0.0.0', () => {
    console.log(`Backend API running on port ${PORT}`);
});
"""
    
    await create_file_in_container(
        container_id=backend_container.id,
        file_path="/workspace/server.js",
        content=backend_server
    )
    
    # Frontend React app setup
    frontend_package_json = {
        "name": "frontend-app",
        "version": "1.0.0",
        "scripts": {
            "start": "react-scripts start",
            "build": "react-scripts build"
        },
        "dependencies": {
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "react-scripts": "5.0.1"
        },
        "proxy": "http://backend-api:3001"
    }
    
    await create_file_in_container(
        container_id=frontend_container.id,
        file_path="/workspace/package.json",
        content=json.dumps(frontend_package_json, indent=2)
    )
    
    # Install dependencies for both containers
    backend_install = await execute_command(
        container_id=backend_container.id,
        command="cd /workspace && npm install"
    )
    
    # Start backend server
    backend_start = await stream_command_execution(
        container_id=backend_container.id,
        command="cd /workspace && npm run dev"
    )
    
    return {
        "backend_container": backend_container.id,
        "frontend_container": frontend_container.id,
        "database_container": db_container.id,
        "backend_ready": backend_install.success
    }

# Execute full-stack setup
fullstack_result = await fullstack_development()
print(f"Full-stack application setup: {fullstack_result}")
```

## Advanced Integration Examples

### Example 9: CI/CD Pipeline Simulation

```python
async def simulate_cicd_pipeline(repo_url, branch="main"):
    """Simulate a complete CI/CD pipeline"""
    
    pipeline_results = {
        "stages": {},
        "overall_success": True
    }
    
    # Stage 1: Code Checkout and Setup
    checkout_container = await create_container(
        image="alpine/git:latest",
        name="checkout-stage"
    )
    
    checkout_result = await execute_command(
        container_id=checkout_container.id,
        command=f"git clone {repo_url} /workspace/code"
    )
    
    pipeline_results["stages"]["checkout"] = {
        "success": checkout_result.success,
        "output": checkout_result.stdout
    }
    
    # Stage 2: Code Quality Analysis
    analysis_container = await create_container(
        image="python:3.11-slim",
        name="analysis-stage"
    )
    
    # Copy code to analysis container
    await copy_file_from_container(
        container_id=checkout_container.id,
        container_path="/workspace/code",
        local_path="./temp_code"
    )
    
    await copy_file_to_container(
        container_id=analysis_container.id,
        local_path="./temp_code",
        container_path="/workspace/code"
    )
    
    # Install analysis tools and run checks
    analysis_setup = await execute_command(
        container_id=analysis_container.id,
        command="pip install pylint black pytest"
    )
    
    lint_result = await execute_command(
        container_id=analysis_container.id,
        command="cd /workspace/code && find . -name '*.py' -exec pylint {} \\;"
    )
    
    format_check = await execute_command(
        container_id=analysis_container.id,
        command="cd /workspace/code && black --check ."
    )
    
    pipeline_results["stages"]["analysis"] = {
        "setup_success": analysis_setup.success,
        "lint_success": lint_result.success,
        "format_success": format_check.success
    }
    
    # Stage 3: Testing
    test_result = await execute_command(
        container_id=analysis_container.id,
        command="cd /workspace/code && python -m pytest --verbose"
    )
    
    pipeline_results["stages"]["testing"] = {
        "success": test_result.success,
        "output": test_result.stdout
    }
    
    # Stage 4: Build (if tests pass)
    if test_result.success:
        build_container = await create_container(
            image="docker:latest",
            name="build-stage"
        )
        
        # Simulate Docker build
        build_result = await execute_command(
            container_id=build_container.id,
            command="echo 'Building Docker image...' && sleep 2 && echo 'Build complete'"
        )
        
        pipeline_results["stages"]["build"] = {
            "success": build_result.success,
            "output": build_result.stdout
        }
    else:
        pipeline_results["stages"]["build"] = {
            "skipped": True,
            "reason": "Tests failed"
        }
    
    # Stage 5: Deployment (simulated)
    if all(stage.get("success", False) for stage in pipeline_results["stages"].values() if "success" in stage):
        deployment_result = {
            "success": True,
            "environment": "staging",
            "timestamp": datetime.now().isoformat()
        }
        pipeline_results["stages"]["deployment"] = deployment_result
    else:
        pipeline_results["stages"]["deployment"] = {
            "skipped": True,
            "reason": "Previous stages failed"
        }
        pipeline_results["overall_success"] = False
    
    # Cleanup containers
    containers_to_cleanup = [checkout_container.id, analysis_container.id]
    if "build_container" in locals():
        containers_to_cleanup.append(build_container.id)
    
    for container_id in containers_to_cleanup:
        await delete_container(container_id=container_id)
    
    return pipeline_results

# Run CI/CD pipeline simulation
# pipeline_result = await simulate_cicd_pipeline("https://github.com/example/python-app.git")
# print(f"Pipeline completed: {pipeline_result['overall_success']}")
```

### Example 10: Multi-Language Performance Comparison

```python
async def performance_comparison():
    """Compare performance of the same algorithm across different languages"""
    
    # Algorithm: Calculate Fibonacci sequence (inefficient recursive version for testing)
    fibonacci_implementations = {
        "python": {
            "image": "python:3.11-slim",
            "code": """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

import time
start_time = time.time()
result = fibonacci(35)
end_time = time.time()
print(f"Result: {result}, Time: {end_time - start_time:.4f} seconds")
""",
            "filename": "fib.py",
            "command": "python fib.py"
        },
        "node": {
            "image": "node:18-alpine",
            "code": """
function fibonacci(n) {
    if (n <= 1) return n;
    return fibonacci(n-1) + fibonacci(n-2);
}

const startTime = Date.now();
const result = fibonacci(35);
const endTime = Date.now();
console.log(`Result: ${result}, Time: ${(endTime - startTime)/1000} seconds`);
""",
            "filename": "fib.js",
            "command": "node fib.js"
        },
        "go": {
            "image": "golang:1.21-alpine",
            "code": """
package main

import (
    "fmt"
    "time"
)

func fibonacci(n int) int {
    if n <= 1 {
        return n
    }
    return fibonacci(n-1) + fibonacci(n-2)
}

func main() {
    start := time.Now()
    result := fibonacci(35)
    elapsed := time.Since(start)
    fmt.Printf("Result: %d, Time: %.4f seconds\\n", result, elapsed.Seconds())
}
""",
            "filename": "fib.go",
            "command": "go run fib.go"
        }
    }
    
    performance_results = {}
    
    for language, config in fibonacci_implementations.items():
        print(f"Testing {language}...")
        
        # Create container for the language
        container = await create_container(
            image=config["image"],
            name=f"perf-test-{language}"
        )
        
        # Create the code file
        await create_file_in_container(
            container_id=container.id,
            file_path=f"/workspace/{config['filename']}",
            content=config["code"]
        )
        
        # Run the performance test
        result = await execute_command(
            container_id=container.id,
            command=f"cd /workspace && {config['command']}"
        )
        
        # Parse the output to extract timing
        output = result.stdout
        performance_results[language] = {
            "success": result.success,
            "output": output,
            "raw_result": result
        }
        
        # Clean up
        await delete_container(container_id=container.id)
    
    # Generate performance report
    print("\nPerformance Comparison Results:")
    print("="*50)
    
    for language, result in performance_results.items():
        if result["success"]:
            print(f"{language.upper()}: {result['output'].strip()}")
        else:
            print(f"{language.upper()}: Failed - {result['output']}")
    
    return performance_results

# Run performance comparison
# perf_results = await performance_comparison()
```

## Monitoring and Debugging Examples

### Example 11: Container Resource Monitoring

```python
async def monitor_container_resources(container_id, duration_minutes=5):
    """Monitor container resources over time"""
    
    monitoring_data = []
    end_time = time.time() + (duration_minutes * 60)
    
    print(f"Monitoring container {container_id} for {duration_minutes} minutes...")
    
    while time.time() < end_time:
        # Get current metrics
        metrics = await get_container_metrics(container_id)
        
        if metrics:
            timestamp = datetime.now()
            monitoring_data.append({
                "timestamp": timestamp,
                "cpu_percent": metrics.get("cpu_percent", 0),
                "memory_usage": metrics.get("memory_usage", "0MB"),
                "memory_percent": metrics.get("memory_percent", 0),
                "network_rx": metrics.get("network_io", {}).get("rx", "0B"),
                "network_tx": metrics.get("network_io", {}).get("tx", "0B")
            })
            
            # Log current status
            print(f"[{timestamp.strftime('%H:%M:%S')}] "
                  f"CPU: {metrics.get('cpu_percent', 0):.1f}% | "
                  f"Memory: {metrics.get('memory_percent', 0):.1f}% "
                  f"({metrics.get('memory_usage', '0MB')})")
        
        # Wait 30 seconds before next measurement
        await asyncio.sleep(30)
    
    # Generate summary report
    if monitoring_data:
        avg_cpu = sum(d["cpu_percent"] for d in monitoring_data) / len(monitoring_data)
        avg_memory = sum(d["memory_percent"] for d in monitoring_data) / len(monitoring_data)
        max_cpu = max(d["cpu_percent"] for d in monitoring_data)
        max_memory = max(d["memory_percent"] for d in monitoring_data)
        
        summary = {
            "duration_minutes": duration_minutes,
            "data_points": len(monitoring_data),
            "average_cpu_percent": avg_cpu,
            "average_memory_percent": avg_memory,
            "peak_cpu_percent": max_cpu,
            "peak_memory_percent": max_memory,
            "detailed_data": monitoring_data
        }
        
        print(f"\nMonitoring Summary:")
        print(f"Average CPU: {avg_cpu:.1f}%")
        print(f"Peak CPU: {max_cpu:.1f}%") 
        print(f"Average Memory: {avg_memory:.1f}%")
        print(f"Peak Memory: {max_memory:.1f}%")
        
        return summary
    
    return {"error": "No monitoring data collected"}

# Example usage:
# monitoring_result = await monitor_container_resources("container_id_here", 3)
```

These examples demonstrate the comprehensive capabilities of the MCP Docker Developer Server across various development scenarios, from basic container operations to complex full-stack development workflows and performance analysis.