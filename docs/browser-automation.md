# Browser Automation with MCPDocker

MCPDocker provides comprehensive browser automation capabilities through both Playwright and Selenium WebDriver integrations. This allows AI assistants to interact with web applications, perform UI testing, and automate web-based tasks within a secure containerized environment.

## 🎭 Playwright Integration

Playwright offers modern, fast, and reliable browser automation with support for Chromium, Firefox, and WebKit.

### Getting Started with Playwright

```python
# Launch a browser
browser_id = await playwright_launch_browser("chromium", headless=True)

# Create a new page
page_id = await playwright_create_page(browser_id)

# Navigate to a website
await playwright_navigate(page_id, "https://example.com")

# Interact with elements
await playwright_click(page_id, "button#submit")
await playwright_type(page_id, "input[name='username']", "user123")

# Take a screenshot
await playwright_screenshot(page_id, "homepage.png")

# Clean up
await playwright_close_page(page_id)
await playwright_close_browser(browser_id)
```

### Playwright Features

- **Cross-browser Support**: Chromium, Firefox, WebKit
- **Fast Execution**: Modern automation engine
- **Advanced Waiting**: Smart element detection
- **JavaScript Evaluation**: Execute custom scripts
- **Screenshot Capabilities**: Full page or element-specific

### Playwright Tools

| Tool | Description |
|------|-------------|
| `playwright_launch_browser` | Launch browser instance |
| `playwright_create_page` | Create new page/tab |
| `playwright_navigate` | Navigate to URL |
| `playwright_click` | Click elements |
| `playwright_type` | Type text into elements |
| `playwright_screenshot` | Take screenshots |
| `playwright_get_text` | Extract text content |
| `playwright_wait_for_selector` | Wait for elements |
| `playwright_evaluate` | Execute JavaScript |
| `playwright_close_page` | Close page |
| `playwright_close_browser` | Close browser |

## 🔧 Selenium Integration

Selenium provides traditional WebDriver automation with extensive browser support and ecosystem compatibility.

### Getting Started with Selenium

```python
# Launch a WebDriver
driver_id = await selenium_launch_driver("chrome", headless=True)

# Navigate to a website
await selenium_navigate(driver_id, "https://example.com")

# Interact with elements
await selenium_click(driver_id, "button#submit", by="css")
await selenium_type(driver_id, "username", "user123", by="id")

# Wait for elements
await selenium_wait_for_element(driver_id, "//div[@class='result']", by="xpath")

# Take a screenshot
await selenium_screenshot(driver_id, "result.png")

# Clean up
await selenium_close_driver(driver_id)
```

### Selenium Features

- **Mature Ecosystem**: Extensive plugin and tool support
- **Multiple Locators**: CSS, XPath, ID, Name, Class, Tag
- **Flexible Waiting**: Various wait conditions
- **JavaScript Execution**: Run custom scripts
- **Wide Browser Support**: Chrome, Firefox, Edge, Safari

### Selenium Tools

| Tool | Description |
|------|-------------|
| `selenium_launch_driver` | Launch WebDriver |
| `selenium_navigate` | Navigate to URL |
| `selenium_click` | Click elements |
| `selenium_type` | Type text into elements |
| `selenium_screenshot` | Take screenshots |
| `selenium_get_text` | Extract text content |
| `selenium_wait_for_element` | Wait for elements |
| `selenium_execute_script` | Execute JavaScript |
| `selenium_close_driver` | Close driver |

## 🎯 Element Selection

### CSS Selectors
```python
# By CSS selector (default for Playwright)
await playwright_click(page_id, "button.primary")
await selenium_click(driver_id, "button.primary", by="css")
```

### XPath
```python
# Selenium XPath support
await selenium_click(driver_id, "//button[contains(text(), 'Submit')]", by="xpath")
```

### Other Selectors (Selenium)
```python
# By ID
await selenium_click(driver_id, "submit-btn", by="id")

# By Name
await selenium_type(driver_id, "username", "user123", by="name")

# By Class Name
await selenium_click(driver_id, "btn-primary", by="class")
```

## 📸 Screenshots and Visual Testing

Both frameworks support screenshot capabilities:

```python
# Playwright - Full page or viewport
await playwright_screenshot(page_id, "full-page.png", full_page=True)

# Selenium - Viewport screenshot
await selenium_screenshot(driver_id, "viewport.png")
```

Screenshots are saved to the shared workspace and can be accessed via the file management tools.

## 🔄 Managing Multiple Browser Instances

```python
# Launch multiple browsers
chrome_driver = await selenium_launch_driver("chrome")
firefox_driver = await selenium_launch_driver("firefox")
chromium_browser = await playwright_launch_browser("chromium")

# List active instances
instances = await list_browser_instances()
# Returns: ["Selenium: sel_chrome_0", "Selenium: sel_firefox_1", "Playwright: pw_chromium_0"]

# Use different browsers for different tasks
await selenium_navigate(chrome_driver, "https://site1.com")
await selenium_navigate(firefox_driver, "https://site2.com")

# Clean up all instances
await selenium_close_driver(chrome_driver)
await selenium_close_driver(firefox_driver)
await playwright_close_browser(chromium_browser)
```

## 🛡️ Security Considerations

- All browser instances run within the MCPDocker environment
- Network access is controlled by Docker container networking
- File system access is limited to the shared workspace
- Browser automation is isolated from the host system
- Headless mode is recommended for production use

## 🎨 Common Use Cases

### Web Scraping
```python
# Launch browser and navigate
browser_id = await playwright_launch_browser("chromium")
page_id = await playwright_create_page(browser_id)
await playwright_navigate(page_id, "https://example.com")

# Extract data
title = await playwright_get_text(page_id, "h1")
await playwright_screenshot(page_id, "scraped-page.png")
```

### Form Automation
```python
# Launch driver and navigate
driver_id = await selenium_launch_driver("chrome")
await selenium_navigate(driver_id, "https://forms.example.com")

# Fill form
await selenium_type(driver_id, "name", "John Doe", by="name")
await selenium_type(driver_id, "email", "john@example.com", by="name")
await selenium_click(driver_id, "submit", by="id")

# Wait for confirmation
await selenium_wait_for_element(driver_id, "success-message", by="class")
```

### UI Testing
```python
# Test user workflow
browser_id = await playwright_launch_browser("chromium")
page_id = await playwright_create_page(browser_id)

# Navigate and test
await playwright_navigate(page_id, "https://app.example.com")
await playwright_click(page_id, "[data-testid='login-button']")
await playwright_type(page_id, "input[type='email']", "test@example.com")
await playwright_type(page_id, "input[type='password']", "password123")
await playwright_click(page_id, "button[type='submit']")

# Verify result
await playwright_wait_for_selector(page_id, "[data-testid='dashboard']")
await playwright_screenshot(page_id, "dashboard-logged-in.png")
```

## 🚀 Performance Tips

1. **Use headless mode** for better performance in automated tasks
2. **Reuse browser instances** when performing multiple operations
3. **Close pages/drivers** promptly to free resources
4. **Use specific selectors** for faster element location
5. **Implement proper waiting** instead of fixed delays

## 🔧 Installation Requirements

Ensure you have the required dependencies installed:

```bash
pip install playwright>=1.40.0 selenium>=4.15.0

# Install Playwright browser binaries
playwright install
```

For Selenium, you'll also need the appropriate WebDriver executables (ChromeDriver, GeckoDriver) or use webdriver-manager for automatic management.