# Docker Tools

The Docker Tools module provides comprehensive container management capabilities, allowing you to create, manage, and interact with Docker containers for safe code testing and development.

## Container Management

### `create_container`
Creates and starts a new Docker container that runs indefinitely.

**Parameters:**
- `image` (required): Docker image name (e.g., "python:3.11-slim"). Must be in the allowed list.
- `name` (optional): Custom name for the container.
- `command` (optional): Custom command to run in the container.
- `environment` (optional): Environment variables as a dictionary.
- `ports` (optional): Port mappings from container to host as a dictionary (e.g., `{"8000": "8080"}`).
- `use_gpu` (optional): Enable GPU access (requires NVIDIA Container Toolkit).

**Returns:** A string confirming the container creation with its name and ID.

**Example:**
```python
await create_container(
    image="python:3.11-slim",
    name="my-python-dev",
    environment={"MY_VAR": "my_value"},
    ports={"8000": 8080}
)
```

### `list_containers`
Lists all active Docker containers.

**Returns:** A JSON string with a list of container information, including ID, name, status, and image.

### `inspect_container`
Inspects a container using the `docker inspect` command.

**Parameters:**
- `container` (required): The name or ID of the container to inspect.

**Returns:** A JSON string with the container's details.

### `start_container`, `stop_container`, `restart_container`
Control the lifecycle of a container.

**Parameters:**
- `container_id` (required): The name or ID of the container to control.

**Returns:** A string confirming the action.

### `delete_container`
Stops and removes a container completely.

**Parameters:**
- `container_id` (required): The name or ID of the container to delete.

**Returns:** A string confirming the deletion.

## Command Execution

### `execute_command`
Execute a command inside a running container.

**Parameters:**
- `container_id` (required): The name or ID of the target container.
- `command` (required): The command to execute.

**Returns:** A string containing the command's exit code and output.

**Example:**
```python
result = await execute_command(
    container_id="my-python-dev",
    command="python -c 'print(\"Hello from container!\")'"
)
```

## Workspace Management

The server provides a shared workspace located at `/tmp/workspace` on the host, which is mounted as `/workspace` inside the containers. You can use `upload_file` and `list_workspace_files` to manage files in this workspace.

### `upload_file`
Upload a file to the shared workspace.

**Parameters:**
- `filename` (required): The name of the file to create in the workspace.
- `content` (required): The content of the file.

**Returns:** A string confirming the file upload.

### `list_workspace_files`
List files in the shared workspace.

**Returns:** A JSON string with a list of files and their details.

## Monitoring and Logging

### `get_container_logs`
Retrieve logs from a container.

**Parameters:**
- `container_id` (required): The name or ID of the target container.
- `tail` (optional): The number of lines to retrieve from the end of the logs (default: 100).

**Returns:** The container logs as a string.

### `get_gpu_status`
Get the status of available NVIDIA and AMD GPUs on the host.

**Returns:** A JSON string with information about the detected GPUs.

## Allowed Images

### `list_allowed_images`
List the Docker images that are allowed to be used for creating containers.

**Returns:** A sorted list of allowed image names.

## Example Workflow

```python
# 1. See what images are available
await list_allowed_images()

# 2. Create a Python development container
await create_container(
    image="python:3.11",
    name="my-app-dev"
)

# 3. Upload a Python script to the workspace
await upload_file(
    filename="app.py",
    content="print('Hello from my app!')"
)

# 4. Execute the script in the container
result = await execute_command(
    container_id="my-app-dev",
    command="python /workspace/app.py"
)
print(result)

# 5. Check the container's logs
logs = await get_container_logs(container_id="my-app-dev")
print(logs)

# 6. Clean up the container
await delete_container(container_id="my-app-dev")
```
