"""
A toolbox with a way to access Documentation using llms.txt files, which is a proposal adopted by some websites.
To learn more, visit https://llmstxt.org
"""
from fastmcp import FastMCP
import requests
class LLMSText():
    def __init__(self):
        pass
    def add_tools(
        self,
        mcp: FastMCP
    ):
        @mcp.tool()
        async def request_llms_txtfile(
            website: str = "",
            context: bool = True,
        ) -> str:
            """
            Retrieve the llms.txt or llms-ctx.txt file from a website.

            Args:
                website (str): The base URL of the website (e.g., "https://example.com").
                context (bool): If True, fetches llms-ctx.txt; if False, fetches llms.txt.

            Returns:
                str: The contents of the requested llms.txt file, or an error/help message.
            """
            if not website:
                return "Error: Please provide a website URL (e.g., https://example.com)."

            # Ensure no trailing slash
            website = website.rstrip("/")

            if context:
                baseurl = f"{website}/llms-ctx.txt"
            else:
                baseurl = f"{website}/llms.txt"

            try:
                response = requests.get(baseurl, timeout=10)
            except Exception as e:
                return f"Error fetching {baseurl}: {e}"

            if response.status_code == 200:
                return response.text
            else:
                return (
                    f"Could not retrieve {baseurl} (status code: {response.status_code}).\n"
                    "Try toggling the 'context' parameter to fetch the other protocol variant."
                )
        @mcp.tool()
        async def learn_more_llms_format(
            context: bool=True
        ):
            if context:
                base_url = f"https://llmstxt.org/llms-ctx.txt"
            else:
                base_url = f"https://llmstxt.org/llms.txt"
            response = requests.get(
                base_url
            )
            if response.status_code == 200:
                return response.text
            else:
                return (
                    "Could not fetch."
                )