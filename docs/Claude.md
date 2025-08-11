# Claude

To Install MCPDocker on Claude, you have to install the Claude Desktop App at https://claude.ai/download. Then, open the settings by opening the Panel and then opening your account. 
- Click on Developer within Desktop Settings. It should not have anything within it.
- Click Edit Config. It should open the claude_desktop_settings.json file. Then, edit and fill out the form using the following template:
```
{
  "mcpServers": {
    "SERVER_NAME": {
      "command": "YOUR_PYTHON_INSTALLATION",
      "args": ["LOCATION_OF_MAINPY"],
      "cwd": "FOLDERLOCATION_OF_MAINPY"
    }
  }
}
```
- If you have set it up correctly, it should show within the Sliders button, it should show your SERVER name.  (Reload Claude).
