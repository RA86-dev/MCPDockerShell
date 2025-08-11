# Claude Desktop Setup

This guide explains how to configure MCPDocker with the Claude Desktop application.

## Prerequisites

1. **MCPDocker installed**: Follow the [Getting Started guide](start.md) first
2. **Claude Desktop App**: [Download here](https://claude.ai/download)

## Step-by-Step Configuration

### 1. Install Claude Desktop
Download and install the Claude Desktop application from https://claude.ai/download

### 2. Access Settings
1. Open Claude Desktop
2. Click on your profile/account in the bottom left
3. Navigate to **Settings** → **Developer**

### 3. Edit Configuration
1. In the Developer section, click **Edit Config**
2. This will open the `claude_desktop_config.json` file in your default text editor

### 4. Add MCPDocker Configuration

Replace the contents with your MCPDocker configuration:

#### Standard Python Installation:
```json
{
  "mcpServers": {
    "mcpdocker": {
      "command": "python",
      "args": ["/full/path/to/MCPDocker/main.py"],
      "cwd": "/full/path/to/MCPDocker"
    }
  }
}
```

#### Using uv (Recommended):
```json
{
  "mcpServers": {
    "mcpdocker": {
      "command": "uv",
      "args": ["run", "main.py"],
      "cwd": "/full/path/to/MCPDocker"
    }
  }
}
```

### 5. Update Paths
Replace the placeholder paths with your actual paths:

**Find your MCPDocker path:**
```bash
cd /path/to/your/MCPDocker
pwd  # This shows your full path
```

**Find your Python path** (if not using uv):
```bash
which python  # On Windows: where python
```

### 6. Example Configurations

#### macOS Example:
```json
{
  "mcpServers": {
    "mcpdocker": {
      "command": "/usr/local/bin/python3",
      "args": ["/Users/username/MCPDocker/main.py"],
      "cwd": "/Users/username/MCPDocker"
    }
  }
}
```

#### Windows Example:
```json
{
  "mcpServers": {
    "mcpdocker": {
      "command": "C:\\Python311\\python.exe",
      "args": ["C:\\Users\\username\\MCPDocker\\main.py"],
      "cwd": "C:\\Users\\username\\MCPDocker"
    }
  }
}
```

#### Linux Example:
```json
{
  "mcpServers": {
    "mcpdocker": {
      "command": "/usr/bin/python3",
      "args": ["/home/username/MCPDocker/main.py"],
      "cwd": "/home/username/MCPDocker"
    }
  }
}
```

### 7. Verify Configuration
1. Save the configuration file
2. **Restart Claude Desktop completely** (close and reopen)
3. Start a new conversation
4. Look for the 🔌 (plug) icon in the input area
5. Click it to see available MCP servers
6. You should see "mcpdocker" listed

## Troubleshooting

### Server Not Appearing
- **Double-check paths**: Ensure all paths are absolute (full paths)
- **Verify permissions**: Make sure Python can execute the main.py file
- **Check Docker**: Ensure Docker is running
- **Restart Claude**: Completely quit and restart Claude Desktop

### Server Error/Not Working
1. **Check logs**: Look in Claude Desktop's developer console for error messages
2. **Test manually**: Run the command from terminal to verify it works:
   ```bash
   cd /path/to/MCPDocker
   python main.py  # or: uv run main.py
   ```
3. **Verify dependencies**: Ensure all Python dependencies are installed

### Path Issues on Windows
- Use **forward slashes** `/` or **double backslashes** `\\` in JSON
- Avoid single backslashes `\` as they are escape characters

### Virtual Environment Issues
If you're using a virtual environment, you have two options:

1. **Use full path to Python in venv:**
   ```json
   {
     "mcpServers": {
       "mcpdocker": {
         "command": "/path/to/venv/bin/python",
         "args": ["/path/to/MCPDocker/main.py"],
         "cwd": "/path/to/MCPDocker"
       }
     }
   }
   ```

2. **Use activation script (Linux/macOS only):**
   ```json
   {
     "mcpServers": {
       "mcpdocker": {
         "command": "/bin/bash",
         "args": ["-c", "source /path/to/venv/bin/activate && python main.py"],
         "cwd": "/path/to/MCPDocker"
       }
     }
   }
   ```

## Success Indicators

When properly configured, you should see:
- 🔌 icon in Claude's message input area
- "mcpdocker" listed when clicking the plug icon
- Ability to run Docker commands through Claude
- Container management capabilities available

## Getting Help

If you continue having issues:
1. Check the [Getting Started guide](start.md) for installation problems
2. Review your configuration file syntax using a JSON validator
3. Test MCPDocker manually from the command line first
