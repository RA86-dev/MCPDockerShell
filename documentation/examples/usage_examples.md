# Usage Examples

This guide provides examples of how to use the MCP Docker Developer Server for various development tasks.

## Example 1: Creating a Python Development Environment

This example shows how to create a Python container, upload a script to it, and execute the script.

```python
import json

# 1. Define the container details
image = "python:3.11"
container_name = "my-python-app"
script_filename = "main.py"
script_content = "print('Hello from a Python script!')"

# 2. Create the container
creation_result = await create_container(
    image=image,
    name=container_name
)
print(f"Container creation result: {creation_result}")

# 3. Upload the Python script to the shared workspace
upload_result = await upload_file(
    filename=script_filename,
    content=script_content
)
print(f"File upload result: {upload_result}")

# 4. Execute the script inside the container
# The workspace is mounted at /workspace in the container
execution_result = await execute_command(
    container_id=container_name,
    command=f"python /workspace/{script_filename}"
)
print(f"Execution result:\\n{execution_result}")

# 5. Clean up the container
delete_result = await delete_container(container_id=container_name)
print(f"Container deletion result: {delete_result}")
```

## Example 2: Researching with the Documentation Tools

This example demonstrates how to use the documentation tools to find information about a topic.

```python
import json

# 1. Search for documentation about "React hooks"
search_results_str = await search_devdocs(
    query="React hooks",
    language="react",
    max_results=3
)
search_results = json.loads(search_results_str)
print("Search results:")
print(json.dumps(search_results, indent=2))

# 2. Get the full content of the first search result
if search_results["results"]:
    first_result = search_results["results"][0]
    path = first_result["path"]
    
    print(f"\\nFetching content for path: {path}...")
    content_str = await get_devdocs_content(
        path=path,
        language="react"
    )
    content = json.loads(content_str)
    
    # Print the first 500 characters of the content
    print(f"Content (first 500 chars):\\n{content['content'][:500]}...")
else:
    print("No search results found.")
```

## Example 3: Running a Web Server in a Container

This example shows how to create a Node.js container, run a simple web server, and expose it to the host.

```python
import json

# 1. Define the container and server details
image = "node:18"
container_name = "my-web-server"
server_filename = "server.js"
server_content = """
const http = require('http');

const server = http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain' });
  res.end('Hello from the web server!\\n');
});

server.listen(8080, '0.0.0.0', () => {
  console.log('Server running at http://0.0.0.0:8080/');
});
"""

# 2. Create the container with a port mapping
# This maps port 8080 in the container to port 8888 on the host
creation_result = await create_container(
    image=image,
    name=container_name,
    ports={"8080": "8888"}
)
print(f"Container creation result: {creation_result}")

# 3. Upload the server script
upload_result = await upload_file(
    filename=server_filename,
    content=server_content
)
print(f"File upload result: {upload_result}")

# 4. Start the server in the background
# We use "nohup ... &" to ensure the process keeps running
execution_result = await execute_command(
    container_id=container_name,
    command=f"nohup node /workspace/{server_filename} > /workspace/server.log 2>&1 &"
)
print(f"Server start command result:\\n{execution_result}")

# 5. Check the server logs to confirm it started
# We add a small delay to give the server time to start
import time
time.sleep(2)
log_result = await execute_command(
    container_id=container_name,
    command="cat /workspace/server.log"
)
print(f"Server log:\\n{log_result}")

print("\\nTo access the server, open http://localhost:8888 in your browser.")
print("Remember to clean up the container when you are finished:")
print(f"await delete_container(container_id='{container_name}')")

```
