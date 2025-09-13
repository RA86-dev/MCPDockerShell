import time
from fastmcp import FastMCP
import os
class MarkdownTools:
    def __init__(self, markdown_path:str="/"):
        self.markdown = markdown_path
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
            fp = open(path,'w') 
            fp.write(artifact)
            return f"success! The data has been written to {filename}."
        @mcp.tool()
        async def save_markdown(
            data: str,
            filename: str
        ):
            """
            Save notes, or any markdown or HTML based languages for future use.

            
            """
            path = f"{self.markdown}/{filename}"
            fp = open(f'{filename}','w')
            fp.write(f'{data}')
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
                f = open(f'{self.artifacts}/{filename}','r')
                return f.read()
            else:
                f = open(f"{self.markdown}",'w')
                return f.read()