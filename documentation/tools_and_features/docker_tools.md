# Docker Tools

The Docker Tools module provides comprehensive container management capabilities, allowing you to create, manage, and interact with Docker containers for safe code testing and development.

## Container Management

### Container Lifecycle

#### `create_container`
Creates and starts a new Docker container that runs indefinitely.

**Parameters:**
- `image` (required): Docker image name (e.g., "python:3.11-slim")
- `name` (optional): Custom name for the container
- `command` (optional): Custom command to run in the container
- `environment` (optional): Environment variables as key-value pairs
- `ports` (optional): Port mappings from container to host
- `use_gpu` (optional): Enable GPU access (requires NVIDIA Container Toolkit)

**Example:**
```python
container = await create_container(
    image="python:3.11-slim",
    name="python-dev",
    environment={"PYTHONPATH": "/workspace"},
    ports={"8000": 8080},
    use_gpu=False
)
```

#### `list_containers`
Lists all active Docker containers managed by the MCP server.

**Returns:** List of container information including ID, name, status, and image.

#### `start_container`, `stop_container`, `restart_container`
Control container lifecycle states.

**Parameters:**
- `container_id` (required): ID of the container to control

#### `delete_container`
Stops and removes a container completely.

**Parameters:**
- `container_id` (required): ID of the container to delete

### Command Execution

#### `execute_command`
Execute a command inside a running container.

**Parameters:**
- `container_id` (required): Target container ID
- `command` (required): Command to execute

**Example:**
```python
result = await execute_command(
    container_id="abc123",
    command="python -c 'print(\"Hello from container!\")'"
)
```

#### `stream_command_execution`
Execute a command and stream the output in real-time.

**Parameters:**
- `container_id` (required): Target container ID
- `command` (required): Command to execute

## File Operations

### Basic File Operations

#### `create_file_in_container`
Create a file with specified content inside a container.

**Parameters:**
- `container_id` (required): Target container ID
- `file_path` (required): Path where to create the file
- `content` (required): File content

#### `read_file_in_container`
Read the contents of a file inside a container.

**Parameters:**
- `container_id` (required): Target container ID
- `file_path` (required): Path to the file to read

#### `write_file_in_container`
Write content to a file inside a container.

**Parameters:**
- `container_id` (required): Target container ID
- `file_path` (required): Target file path
- `content` (required): Content to write
- `append` (optional): Whether to append to existing file (default: false)

#### `delete_file_in_container`
Delete a file inside a container.

**Parameters:**
- `container_id` (required): Target container ID
- `file_path` (required): Path to the file to delete

### Directory Operations

#### `list_files_in_container`
List files and directories in a container directory.

**Parameters:**
- `container_id` (required): Target container ID
- `directory_path` (optional): Directory path (default: "/workspace")

#### `create_directory_in_container`
Create a directory inside a container.

**Parameters:**
- `container_id` (required): Target container ID
- `directory_path` (required): Path of the directory to create

### File Transfer Operations

#### `copy_file_to_container`
Copy a file from local filesystem or workspace to a container.

**Parameters:**
- `container_id` (required): Target container ID
- `local_path` (required): Source file path on local system
- `container_path` (required): Destination path in container

#### `copy_file_from_container`
Copy a file from container to local workspace.

**Parameters:**
- `container_id` (required): Source container ID
- `container_path` (required): Source file path in container
- `local_path` (optional): Destination path (if not specified, uses workspace)

#### `copy_file_in_container`, `move_file_in_container`
Copy or move files within a container.

**Parameters:**
- `container_id` (required): Target container ID
- `source_path` (required): Source file/directory path
- `dest_path` (required): Destination path

## Monitoring and Logging

#### `get_container_logs`
Retrieve logs from a container.

**Parameters:**
- `container_id` (required): Target container ID
- `tail` (optional): Number of lines to retrieve (default: 100)

#### `stream_container_logs`
Stream container logs in real-time.

**Parameters:**
- `container_id` (required): Target container ID
- `follow` (optional): Continue streaming new logs (default: true)
- `tail` (optional): Number of historical lines to include (default: 100)

## Networking and Port Management

#### `start_port_stream`
Start streaming data from a container port to a host port.

**Parameters:**
- `container_id` (required): Target container ID
- `container_port` (required): Container port to stream from
- `host_port` (optional): Host port to stream to (auto-assigned if not specified)

#### `stop_port_stream`
Stop streaming data from a container port.

**Parameters:**
- `container_id` (required): Target container ID
- `container_port` (required): Container port to stop streaming

#### `list_active_streams`
List all active port streams.

## Security Features

### Docker Scout Integration

#### `scout_scan_vulnerabilities`
Scan a Docker image for security vulnerabilities using Docker Scout.

**Parameters:**
- `image` (required): Docker image name to scan

#### `scout_get_recommendations`
Get Docker Scout security recommendations for an image.

**Parameters:**
- `image` (required): Docker image name

#### `scout_quickview`
Get a quick security overview of a Docker image.

**Parameters:**
- `image` (required): Docker image name

#### `scout_compare_images`
Compare two Docker images for security differences.

**Parameters:**
- `base_image` (required): Base image for comparison
- `target_image` (required): Target image for comparison

#### `scout_policy_evaluation`
Evaluate a Docker image against security policies.

**Parameters:**
- `image` (required): Docker image name
- `policy` (optional): Security policy name (default: "default")

## Workspace Management

#### `upload_file`
Upload a file to the shared workspace accessible by containers.

**Parameters:**
- `filename` (required): Name of the file
- `content` (required): File content

#### `list_workspace_files`
List files in the shared workspace.

## GPU Support

When `use_gpu=True` is specified during container creation:

- Enables NVIDIA GPU access within containers
- Requires NVIDIA Container Toolkit to be installed on the host
- Useful for AI/ML workloads requiring GPU acceleration
- Check GPU availability with `get_gpu_status()`

## Supported Images

Use `list_allowed_images()` to see which Docker images are available for container creation. The system supports a wide range of programming language environments including:

- Python (various versions)
- Node.js
- Java
- Go
- Rust
- And many more

## Best Practices

1. **Resource Management**: Always clean up containers when done using `delete_container()`
2. **Security**: Use minimal base images and scan with Docker Scout
3. **Networking**: Use port streaming for web applications and services
4. **File Operations**: Use the workspace for sharing files between host and containers
5. **Monitoring**: Monitor container logs and resource usage regularly

## Example Workflow

```python
# Create a Python development container
container = await create_container(
    image="python:3.11-slim",
    name="python-dev"
)

# Create a Python script
await create_file_in_container(
    container_id=container.id,
    file_path="/workspace/hello.py",
    content="print('Hello from Docker!')"
)

# Execute the script
result = await execute_command(
    container_id=container.id,
    command="python /workspace/hello.py"
)

# Check logs
logs = await get_container_logs(container_id=container.id)

# Clean up
await delete_container(container_id=container.id)
```