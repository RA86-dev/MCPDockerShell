from fastmcp import FastMCP


class PromptManager:
    def __init__(self):
        pass # nothing is needed here.
    
    def add_prompt(self, mcp_server: FastMCP):
        @mcp_server.prompt()
        def GenerateCode(what_to_build: str, language: list, other_notes: str):
            """
            A prompt specially made for this MCP server. Provide a bunch of languages you want to use and what to build, and it will build it for you.
            """
            language_str = ""
            for item in language:
                language_str += f' - {item}\n'
            
            prompt = f"""You are an expert Software Developer and System Architect with extensive experience across multiple programming languages and frameworks.

## Project Requirements
**What to Build:** {what_to_build}

**Target Languages/Technologies:**
{language_str}

**Additional Notes:** {other_notes}

## Your Task
Please develop a complete, production-ready solution that meets the following criteria:

### Code Quality Standards
- Write clean, maintainable, and well-documented code
- Follow language-specific best practices and conventions
- Include proper error handling and edge case management
- Implement appropriate design patterns where beneficial
- Ensure code is scalable and performant
### Tools
1. Use the MCP Server for research the syntax, (DevDocs), Firecrawl (If avaliable), and SearXNG. These tools are specially made for you to be more accurate.
2. Use Docker Containerization to run containers. DO not run any scripts that run forever, e.g. servers. It will freeze the conversation.
### Deliverables
1. **Architecture Overview**: Brief explanation of your chosen architecture and design decisions
2. **Complete Implementation**: Fully functional code with all necessary files
3. **Documentation**: Clear setup instructions, usage examples, and API documentation if applicable
4. **Testing**: Include unit tests or testing strategy recommendations
5. **Deployment Notes**: Instructions for deployment and any configuration requirements

### Technical Considerations
- Use modern language features and libraries appropriately
- Consider security best practices
- Optimize for the specified use case
- Ensure cross-platform compatibility where relevant
- Include proper dependency management

### Code Structure
- Organize code into logical modules/components
- Use meaningful variable and function names
- Add inline comments for complex logic
- Include type hints/annotations where supported by the language

Please provide a comprehensive solution that a developer could immediately use and deploy. If you need clarification on any requirements, ask specific questions to ensure the solution meets the exact needs."""

            return prompt
        @mcp_server.prompt()
        def FixError(ErrorLogs: str, language: str, other_notes: str):
            prompt = f"""
You are a Professional Developer, and you have found an error in the code! You need to fix the error. The user has provided some logs:
{ErrorLogs}
## language:
{language}
## Other Notes:
{other_notes}
### Tools
1. Use the Docker tool to test the new version of the code.
2. Use SearXNG, Firecrawl (if avaliable), and Documentation to create a cohesive report.
### Expected Response
Please provide a Report, on why the error has happened, and information on a fix to the code.

"""
            return str(prompt)