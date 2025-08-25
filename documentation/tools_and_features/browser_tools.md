# Browser Tools

The Browser Tools module provides comprehensive web automation capabilities using both Playwright and Selenium WebDriver. These tools enable you to interact with web applications, perform automated testing, and capture screenshots for analysis.

## Playwright Tools

Playwright provides modern, reliable browser automation with support for Chromium, Firefox, and WebKit.

### Browser Management

#### `playwright_launch_browser`
Launches a new Playwright browser instance.

**Parameters:**
- `browser_type` (optional): Browser type - "chromium", "firefox", or "webkit" (default: "chromium")
- `headless` (optional): Run browser in headless mode (default: true)
- `args` (optional): Additional browser arguments

**Example:**
```python
browser = await playwright_launch_browser(
    browser_type="chromium",
    headless=False,
    args=["--disable-web-security"]
)
```

#### `playwright_close_browser`
Close a Playwright browser instance.

**Parameters:**
- `browser_id` (required): ID of the browser to close

### Page Management

#### `playwright_create_page`
Creates a new page in a Playwright browser.

**Parameters:**
- `browser_id` (required): ID of the browser
- `viewport_width` (optional): Page width in pixels (default: 1920)
- `viewport_height` (optional): Page height in pixels (default: 1080)

#### `playwright_close_page`
Close a Playwright page.

**Parameters:**
- `page_id` (required): ID of the page to close

### Navigation and Interaction

#### `playwright_navigate`
Navigate to a URL in a Playwright page.

**Parameters:**
- `page_id` (required): Target page ID
- `url` (required): URL to navigate to
- `wait_until` (optional): When to consider navigation finished - "load", "domcontentloaded", "networkidle" (default: "load")

#### `playwright_click`
Click an element on a Playwright page.

**Parameters:**
- `page_id` (required): Target page ID
- `selector` (required): CSS selector for the element
- `timeout` (optional): Timeout in milliseconds (default: 30000)

#### `playwright_type`
Type text into an element on a Playwright page.

**Parameters:**
- `page_id` (required): Target page ID
- `selector` (required): CSS selector for the input element
- `text` (required): Text to type
- `timeout` (optional): Timeout in milliseconds (default: 30000)

#### `playwright_get_text`
Get text content from an element on a Playwright page.

**Parameters:**
- `page_id` (required): Target page ID
- `selector` (required): CSS selector for the element
- `timeout` (optional): Timeout in milliseconds (default: 30000)

### Waiting and Synchronization

#### `playwright_wait_for_selector`
Wait for an element to appear on a Playwright page.

**Parameters:**
- `page_id` (required): Target page ID
- `selector` (required): CSS selector to wait for
- `state` (optional): Element state to wait for - "attached", "detached", "visible", "hidden" (default: "visible")
- `timeout` (optional): Timeout in milliseconds (default: 30000)

### Screenshots and Visual Testing

#### `playwright_screenshot`
Take a screenshot of a Playwright page.

**Parameters:**
- `page_id` (required): Target page ID
- `filename` (optional): Filename to save the screenshot
- `full_page` (optional): Capture full page height (default: false)
- `return_base64` (optional): Return screenshot as base64 for AI analysis (default: false)

### JavaScript Execution

#### `playwright_evaluate`
Execute JavaScript in a Playwright page context.

**Parameters:**
- `page_id` (required): Target page ID
- `script` (required): JavaScript code to execute

**Example:**
```python
result = await playwright_evaluate(
    page_id=page.id,
    script="document.title"
)
```

## Selenium Tools

Selenium WebDriver provides robust cross-browser automation with support for Chrome and Firefox.

### Driver Management

#### `selenium_launch_driver`
Launch a Selenium WebDriver instance.

**Parameters:**
- `browser_type` (optional): Browser type - "chrome" or "firefox" (default: "chrome")
- `headless` (optional): Run browser in headless mode (default: true)
- `options` (optional): Additional browser options

#### `selenium_close_driver`
Close a Selenium driver instance.

**Parameters:**
- `driver_id` (required): ID of the driver to close

### Navigation and Interaction

#### `selenium_navigate`
Navigate to a URL using Selenium.

**Parameters:**
- `driver_id` (required): Target driver ID
- `url` (required): URL to navigate to

#### `selenium_click`
Click an element using Selenium.

**Parameters:**
- `driver_id` (required): Target driver ID
- `selector` (required): Element selector
- `by` (optional): Selector type - "css", "xpath", "id", "name", "tag_name", "class_name", "link_text" (default: "css")
- `timeout` (optional): Timeout in seconds (default: 10)

#### `selenium_type`
Type text into an element using Selenium.

**Parameters:**
- `driver_id` (required): Target driver ID
- `selector` (required): Element selector
- `text` (required): Text to type
- `by` (optional): Selector type (default: "css")
- `clear` (optional): Clear existing text first (default: true)
- `timeout` (optional): Timeout in seconds (default: 10)

#### `selenium_get_text`
Get text content from an element using Selenium.

**Parameters:**
- `driver_id` (required): Target driver ID
- `selector` (required): Element selector
- `by` (optional): Selector type (default: "css")
- `timeout` (optional): Timeout in seconds (default: 10)

### Waiting

#### `selenium_wait_for_element`
Wait for an element using Selenium.

**Parameters:**
- `driver_id` (required): Target driver ID
- `selector` (required): Element selector
- `by` (optional): Selector type (default: "css")
- `condition` (optional): Wait condition - "presence", "visible", "clickable" (default: "presence")
- `timeout` (optional): Timeout in seconds (default: 10)

### Screenshots

#### `selenium_screenshot`
Take a screenshot using Selenium.

**Parameters:**
- `driver_id` (required): Target driver ID
- `filename` (optional): Filename to save the screenshot

### JavaScript Execution

#### `selenium_execute_script`
Execute JavaScript using Selenium.

**Parameters:**
- `driver_id` (required): Target driver ID
- `script` (required): JavaScript code to execute

## Browser Instance Management

#### `list_browser_instances`
List all active browser instances (both Playwright and Selenium).

#### `share_screenshot_with_ai`
Share a screenshot file with AI for analysis by returning it as base64.

**Parameters:**
- `filename` (required): Screenshot filename to share

## Use Cases

### Web Application Testing
- Automated UI testing
- Form submission testing
- Navigation flow validation
- Cross-browser compatibility testing

### Web Scraping
- Data extraction from websites
- Content monitoring
- Dynamic content handling
- Multi-page workflows

### Visual Testing
- Screenshot comparison
- Layout validation
- Responsive design testing
- Visual regression testing

### Performance Testing
- Page load time measurement
- Resource loading analysis
- Interactive element testing

## Example Workflows

### Basic Web Automation with Playwright
```python
# Launch browser and create page
browser = await playwright_launch_browser(browser_type="chromium")
page = await playwright_create_page(browser_id=browser.id)

# Navigate and interact
await playwright_navigate(page_id=page.id, url="https://example.com")
await playwright_click(page_id=page.id, selector="#login-button")
await playwright_type(page_id=page.id, selector="#username", text="testuser")

# Take screenshot
screenshot = await playwright_screenshot(
    page_id=page.id,
    filename="test-result.png",
    return_base64=True
)

# Clean up
await playwright_close_page(page_id=page.id)
await playwright_close_browser(browser_id=browser.id)
```

### Cross-Browser Testing with Selenium
```python
# Test with multiple browsers
browsers = ["chrome", "firefox"]

for browser_type in browsers:
    driver = await selenium_launch_driver(browser_type=browser_type)
    await selenium_navigate(driver_id=driver.id, url="https://myapp.com")
    
    # Perform tests
    await selenium_click(driver_id=driver.id, selector="#test-button")
    result = await selenium_get_text(driver_id=driver.id, selector="#result")
    
    # Take screenshot for comparison
    await selenium_screenshot(
        driver_id=driver.id,
        filename=f"test-{browser_type}.png"
    )
    
    await selenium_close_driver(driver_id=driver.id)
```

## Best Practices

1. **Choose the Right Tool**: Use Playwright for modern web apps, Selenium for broader compatibility
2. **Proper Cleanup**: Always close browsers and pages when done
3. **Error Handling**: Use appropriate timeouts and handle element not found scenarios
4. **Screenshots**: Capture screenshots for debugging and visual verification
5. **Headless Mode**: Use headless mode for CI/CD environments
6. **Selector Strategy**: Prefer stable CSS selectors or data attributes over xpath
