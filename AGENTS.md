# AGENTS.md

This file provides instructions and guidelines for agents working with the MCP Developer Server codebase.

## Project Structure

The project is organized into the following main directories:

- `documentation/`: Contains user-facing documentation.
- `subtools/`: Contains the core logic for the different toolsets (Docker, documentation, etc.).
- `static_assets/`: Contains static files, such as `settings.yml` and agent context files.
- `main.py`: The main entry point for the server.
- `Dockerfile`: Used to build the main application Docker image.
- `compose.yml`: Defines the Docker Compose services for the server and its dependencies.

## Development Workflow

1.  **Explore the Codebase:** Before making any changes, familiarize yourself with the relevant files. The `subtools/` directory is a good place to start for understanding the core logic.
2.  **Make Changes:** When adding or modifying features, ensure that you follow the existing coding style and conventions.
3.  **Update Documentation:** If you add or change a tool, you **must** update the user-facing documentation in the `documentation/` directory. Create a `USAGE.md` if it does not exist.
4.  **Run Tests:** Although there is no formal test suite yet, you should manually test your changes to ensure they work as expected and do not break existing functionality.
5.  **Submit for Review:** Once your changes are complete and tested, request a code review.

## Coding Conventions

- **Error Handling:** When a tool encounters an error, it should return a structured JSON response with an "error" key. For example: `{"error": "Something went wrong"}`. Do not return plain text error messages.
- **Configuration:** Avoid hardcoding configurations. If a value is likely to change, move it to a configuration file (e.g., `configuration.json` or a new domain-specific config file).
- **Logging:** Use the provided logger (`self.logger`) to log important events, warnings, and errors. This is crucial for debugging.
- **Docstrings:** All new functions and classes should have clear and concise docstrings.

## Running the Server

The server is designed to be run with Docker Compose. To start the server, use the following command:

```bash
docker compose up -d --build
```

This will start the main MCP server, the `devdocs` service, and the `devdocs-sync` service.

## Key Files to Understand

- `main.py`: The heart of the application. It initializes all the tool modules and registers the tools with the `FastMCP` server.
- `subtools/docker_tools.py`: Manages all Docker-related operations. This is a critical component.
- `subtools/documentation_tools.py`: Handles all documentation-related features, including searching DevDocs and accessing local documentation.
- `compose.yml`: Defines the multi-service Docker environment. Understanding this file is key to understanding how the different parts of the application interact.
- `configuration.json`: Main configuration for the server.
