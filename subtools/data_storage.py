import time
from fastmcp import FastMCP
import os
class MarkdownTools:
    def __init__(self, markdown_path:str="/"):
        self.base_path = markdown_path
        os.makedirs(exist_ok=True, name=f'{markdown_path}/artifacts')
        os.makedirs(exist_ok=True, name=f'{markdown_path}/markdown')
        os.makedirs(exist_ok=True, name=f'{markdown_path}/other_data')
        self.artifacts = f'{markdown_path}/artifacts'
        self.markdown = f'{markdown_path}/markdown'
        self.other_data = f'{markdown_path}/other_data'
    def add_mcp_tools(self, mcp: FastMCP):
        @mcp.tool()
        async def save_artifact(
            artifact: str,
            filename: str=f"{time.asctime()}"
        ):
            """
            Saves any code based languages, e.g. Python or Go.
            Recommended only for Artifacts or sections of code.
            """
            path = f"{self.artifacts}/{filename}"
            with open(path, 'w') as fp:
                fp.write(artifact)
            return f"success! The data has been written to {filename}."
        @mcp.tool()
        async def save_markdown(
            data: str,
            filename: str
        ):
            """
            Save notes, or any markdown or HTML based languages for future use.
            Only Markdown please!
            
            """
            if data.split('.')[1] != ".md":
                return "Only Markdown supported."
            path = f"{self.markdown}/{filename}"
            with open(path, 'w') as fp:
                fp.write(data)
            return f"success! The data has been written to {filename}"
        @mcp.tool()
        async def list(
        ):
            """
            Shows the entire content of the Markdown and Artifacts directory from the save_markdown and save_artifact features.

            
            """
            artifacts = os.listdir(self.artifacts)
            markdowns = os.listdir(self.markdown)
            return {
                "artifacts":artifacts,
                "markdowns":markdowns
            }
        @mcp.tool()
        async def read(
            filename: str,
            artifact: bool
        ):
            """
            Reads a file from the directories. Please specify if it is a Artifact or if its a note.
            artifact: bool - Please change this to positive for Artifacts, false for Notes or Markdown.
            
            """
            if artifact:
                with open(f'{self.artifacts}/{filename}', 'r') as f:
                    return f.read()
            else:
                with open(f'{self.markdown}/{filename}', 'r') as f:
                    return f.read()