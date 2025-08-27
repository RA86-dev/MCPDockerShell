"""
Browser automation tools using Playwright and Selenium
"""
import json
import secrets
import base64
from typing import Dict, Any, Optional, List
from pathlib import Path
from notify import ntfyClient
# Optional imports
try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    HAS_SELENIUM = True
except ImportError:
    HAS_SELENIUM = False


class BrowserTools:
    """Browser automation functionality using Playwright and Selenium"""

    def __init__(self, temp_dir: str, logger=None):
        self.temp_dir = Path(temp_dir)
        self.logger = logger
        self.playwright_instance = None
        self.active_browsers = {}
        self.active_selenium_drivers = {}

    def register_tools(self, mcp_server):
        """Register browser automation tools with the MCP server"""

        # Playwright tools
        @mcp_server.tool()
        async def playwright_launch_browser(
            browser_type: str = "chromium",
            headless: bool = True,
            args: List[str] = None
        ) -> str:
            """Launch a new Playwright browser instance (chromium, firefox, or webkit). Supports headless, so try to use Headless."""
            if not HAS_PLAYWRIGHT:
                return "Error: Playwright not installed. Install with: pip install playwright"

            try:
                if not self.playwright_instance:
                    self.playwright_instance = await async_playwright().start()

                if browser_type not in ["chromium", "firefox", "webkit"]:
                    return f"Error: Unsupported browser type '{browser_type}'. Use: chromium, firefox, or webkit"

                browser_launcher = getattr(self.playwright_instance, browser_type)
                launch_options = {"headless": headless}

                if args:
                    launch_options["args"] = args

                browser = await browser_launcher.launch(**launch_options)
                browser_id = f"{browser_type}_{secrets.token_hex(8)}"

                self.active_browsers[browser_id] = {
                    "browser": browser,
                    "type": browser_type,
                    "pages": {}
                }

                return f"Browser launched successfully: {browser_id}"

            except Exception as e:
                return f"Error launching browser: {str(e)}"

        @mcp_server.tool()
        async def playwright_create_page(
            browser_id: str,
            viewport_width: int = 1920,
            viewport_height: int = 1080
        ) -> str:
            """Create a new page in a Playwright browser"""
            if browser_id not in self.active_browsers:
                return f"Browser {browser_id} not found"

            try:
                browser_info = self.active_browsers[browser_id]
                page = await browser_info["browser"].new_page()
                await page.set_viewport_size({"width": viewport_width, "height": viewport_height})

                page_id = f"page_{secrets.token_hex(8)}"
                browser_info["pages"][page_id] = page

                return f"Page created successfully: {page_id}"

            except Exception as e:
                return f"Error creating page: {str(e)}"

        @mcp_server.tool()
        async def playwright_navigate(browser_id: str, page_id: str, url: str, wait_until: str = "load") -> str:
            """Navigate to a URL in a Playwright page"""
            page = self._get_playwright_page(browser_id, page_id)
            if isinstance(page, str):
                return page

            try:
                await page.goto(url, wait_until=wait_until)
                return f"Navigated to {url} successfully"
            except Exception as e:
                return f"Error navigating to {url}: {str(e)}"

        @mcp_server.tool()
        async def playwright_click(browser_id: str, page_id: str, selector: str, timeout: int = 30000) -> str:
            """Click an element on a Playwright page"""
            page = self._get_playwright_page(browser_id, page_id)
            if isinstance(page, str):
                return page

            try:
                await page.click(selector, timeout=timeout)
                return f"Clicked element: {selector}"
            except Exception as e:
                return f"Error clicking element {selector}: {str(e)}"

        @mcp_server.tool()
        async def playwright_type(browser_id: str, page_id: str, selector: str, text: str, timeout: int = 30000) -> str:
            """Type text into an element on a Playwright page"""
            page = self._get_playwright_page(browser_id, page_id)
            if isinstance(page, str):
                return page

            try:
                await page.fill(selector, text, timeout=timeout)
                return f"Typed text into {selector}"
            except Exception as e:
                return f"Error typing into {selector}: {str(e)}"

        @mcp_server.tool()
        async def playwright_screenshot(
            browser_id: str,
            page_id: str,
            filename: str = None,
            full_page: bool = False,
            return_base64: bool = False
        ) -> str:
            """Take a screenshot of a Playwright page"""
            page = self._get_playwright_page(browser_id, page_id)
            if isinstance(page, str):
                return page

            try:
                screenshot_options = {"full_page": full_page}

                if filename:
                    filepath = self.temp_dir / filename
                    screenshot_options["path"] = str(filepath)
                    await page.screenshot(**screenshot_options)
                    result = f"Screenshot saved: {filename}"
                else:
                    screenshot_bytes = await page.screenshot(**screenshot_options)
                    if return_base64:
                        screenshot_b64 = base64.b64encode(screenshot_bytes).decode()
                        return f"data:image/png;base64,{screenshot_b64}"
                    else:
                        filename = f"screenshot_{secrets.token_hex(8)}.png"
                        filepath = self.temp_dir / filename
                        with open(filepath, "wb") as f:
                            f.write(screenshot_bytes)
                        result = f"Screenshot saved: {filename}"

                return result

            except Exception as e:
                return f"Error taking screenshot: {str(e)}"

        @mcp_server.tool()
        async def playwright_get_text(browser_id: str, page_id: str, selector: str, timeout: int = 30000) -> str:
            """Get text content from an element on a Playwright page"""
            page = self._get_playwright_page(browser_id, page_id)
            if isinstance(page, str):
                return page

            try:
                element = await page.wait_for_selector(selector, timeout=timeout)
                text = await element.text_content()
                return text or ""
            except Exception as e:
                return f"Error getting text from {selector}: {str(e)}"

        # Selenium tools
        @mcp_server.tool()
        async def selenium_launch_driver(
            browser_type: str = "chrome",
            headless: bool = True,
            options: List[str] = None
        ) -> str:
            """Launch a Selenium WebDriver (chrome or firefox)"""
            if not HAS_SELENIUM:
                return "Error: Selenium not installed. Install with: pip install selenium"

            try:
                driver_id = f"{browser_type}_{secrets.token_hex(8)}"

                if browser_type == "chrome":
                    chrome_options = ChromeOptions()
                    if headless:
                        chrome_options.add_argument("--headless")
                    chrome_options.add_argument("--no-sandbox")
                    chrome_options.add_argument("--disable-dev-shm-usage")

                    if options:
                        for option in options:
                            chrome_options.add_argument(option)

                    driver = webdriver.Chrome(options=chrome_options)

                elif browser_type == "firefox":
                    firefox_options = FirefoxOptions()
                    if headless:
                        firefox_options.add_argument("--headless")

                    if options:
                        for option in options:
                            firefox_options.add_argument(option)

                    driver = webdriver.Firefox(options=firefox_options)

                else:
                    return f"Error: Unsupported browser type '{browser_type}'. Use: chrome or firefox"

                self.active_selenium_drivers[driver_id] = {
                    "driver": driver,
                    "type": browser_type
                }

                return f"Selenium driver launched successfully: {driver_id}"

            except Exception as e:
                return f"Error launching Selenium driver: {str(e)}"

        @mcp_server.tool()
        async def selenium_navigate(driver_id: str, url: str) -> str:
            """Navigate to a URL using Selenium"""
            if driver_id not in self.active_selenium_drivers:
                return f"Selenium driver {driver_id} not found"

            try:
                driver = self.active_selenium_drivers[driver_id]["driver"]
                driver.get(url)
                return f"Navigated to {url} successfully"
            except Exception as e:
                return f"Error navigating to {url}: {str(e)}"

        @mcp_server.tool()
        async def selenium_click(driver_id: str, selector: str, by: str = "css", timeout: int = 10) -> str:
            """Click an element using Selenium"""
            if driver_id not in self.active_selenium_drivers:
                return f"Selenium driver {driver_id} not found"

            try:
                driver = self.active_selenium_drivers[driver_id]["driver"]
                wait = WebDriverWait(driver, timeout)

                by_method = getattr(By, by.upper(), By.CSS_SELECTOR)
                element = wait.until(EC.element_to_be_clickable((by_method, selector)))
                element.click()

                return f"Clicked element: {selector}"
            except Exception as e:
                return f"Error clicking element {selector}: {str(e)}"

        @mcp_server.tool()
        async def selenium_type(
            driver_id: str,
            selector: str,
            text: str,
            by: str = "css",
            clear: bool = True,
            timeout: int = 10
        ) -> str:
            """Type text into an element using Selenium"""
            if driver_id not in self.active_selenium_drivers:
                return f"Selenium driver {driver_id} not found"

            try:
                driver = self.active_selenium_drivers[driver_id]["driver"]
                wait = WebDriverWait(driver, timeout)

                by_method = getattr(By, by.upper(), By.CSS_SELECTOR)
                element = wait.until(EC.presence_of_element_located((by_method, selector)))

                if clear:
                    element.clear()
                element.send_keys(text)

                return f"Typed text into {selector}"
            except Exception as e:
                return f"Error typing into {selector}: {str(e)}"

        @mcp_server.tool()
        async def list_browser_instances() -> str:
            """List all active browser instances"""
            instances = {
                "playwright_browsers": list(self.active_browsers.keys()),
                "selenium_drivers": list(self.active_selenium_drivers.keys())
            }
            return json.dumps(instances, indent=2)

    def _get_playwright_page(self, browser_id: str, page_id: str):
        """Helper to get Playwright page"""
        if browser_id not in self.active_browsers:
            return f"Browser {browser_id} not found"

        browser_info = self.active_browsers[browser_id]
        if page_id not in browser_info["pages"]:
            return f"Page {page_id} not found in browser {browser_id}"

        return browser_info["pages"][page_id]
