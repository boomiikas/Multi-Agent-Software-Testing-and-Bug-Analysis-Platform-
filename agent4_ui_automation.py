import os
import re
import json
import difflib
import traceback
from langchain_ollama import OllamaLLM
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Model specification: Gemma 3 4B
llm_ui = OllamaLLM(model="gemma3:4b")


def ui_automation_agent(state: dict) -> dict:
    """
    Agent 4: Dynamically extracts element selectors from SRS context & test cases
    to generate valid Playwright Python script statements.
    """
    srs_document = state.get("srs_document", "")
    test_cases = state.get("test_cases", [])
    target_url = state.get("target_url", "")
    
    tc_text = (
        test_cases[0].get("details", str(test_cases))
        if (isinstance(test_cases, list) and test_cases)
        else str(test_cases)
    )

    prompt = f"""
You are an expert Playwright UI Automation Agent writing executable Python code for Chromium browser tests.

[TEST CASES TO AUTOMATE]:
{tc_text}

[TARGET URL]:
{target_url}

[TARGET APPLICATION SPECIFICATIONS / SRS DOCUMENT]:
{srs_document}

[CRITICAL SELECTOR MAPPING RULES]:
- ALWAYS map the login Username field to selector: "input#user-name" (NEVER use "input#username" or "#username").
- ALWAYS map the login Password field to selector: "input#password" (NEVER use "input#pass" or "#password").
- ALWAYS map the login button to selector: "input#login-button" (NEVER click "#continue" to login).
- ALWAYS map the checkout continue button to selector: "input#continue".
- ALWAYS map the checkout finish button to selector: "button#finish".
- ALWAYS map the Cart Quantity Badge to selector: "span.shopping_cart_badge" (NEVER use "#shopping_cart_badge").
- NEVER guess or make up CSS class selectors like "a.btn--primary", "a.btn--secondary", ".btn_primary", etc. (instead, look up the exact selectors from the SRS document UI Selector Reference Table, e.g. "button#add-to-cart-sauce-labs-backpack").

[FEW-SHOT SYNTAX EXAMPLE]:
```python
await page.fill("input#user-name", "standard_user")
await page.fill("input#password", "secret_sauce")
await page.click("input#login-button")
await page.wait_for_url("/inventory.html")
await page.click("button#add-to-cart-sauce-labs-backpack")
await page.locator("span.shopping_cart_badge").wait_for(state="visible")
await page.click("a.shopping_cart_link")
await page.click("button#checkout")
await page.fill("input#first-name", "John")
await page.fill("input#last-name", "Doe")
await page.fill("input#postal-code", "12345")
await page.click("input#continue")
await page.click("button#finish")
```

TASK:
Write sequential Playwright automation statements in Python async syntax based STRICTLY on the element selectors and flow given in the SRS document above.

STRICT STYLING RULES:
1. EXCLUSIVELY output executable Python statements. NEVER comment out code lines using `#`.
2. EXCLUSIVELY use the exact CSS selectors, element IDs, or attributes explicitly specified in the SRS document.
3. NEVER guess or invent element selectors if they are not present in the SRS document.
4. NEVER use keyword arguments like `locator=` or `text=` inside methods.
   - WRONG: await page.click(locator="#login-button")
   - RIGHT: await page.click("#login-button")
5. DO NOT include `try:`, `except:`, `finally:`, or `if __name__ == "__main__":` blocks.
6. DO NOT define helper functions (NO `async def...`).
7. DO NOT write browser setup code. Assume `page` is already open and navigated to `{target_url}`.
8. Standard Playwright Python API usage:
   - `page.url` (property, NOT `page.url()`)
   - `await page.goto(url)`
   - `await page.fill(selector, text)`
   - `await page.click(selector)`
   - `await page.wait_for_url(url_pattern)`
9. Output ONLY executable Python code inside a ```python ``` block. No conversational text.
"""
    
    code_response = llm_ui.invoke(prompt)
    
    script = code_response
    if "```python" in script:
        script = script.split("```python")[1].split("```")[0].strip()
    elif "```" in script:
        script = script.split("```")[1].split("```")[0].strip()
        
    return {"ui_script": script}


def _clean_and_indent_script(code_str: str) -> str:
    """
    Sanitizes LLM output dynamically without application-specific hardcoding,
    ensuring Python code contains valid executable indented blocks.
    """
    # 1. Scrub keyword argument hallucinations: convert click(locator="...") -> click("...")
    # Matches locator=, selector=, text=, value= when preceded by a comma or opening parenthesis.
    code_str = re.sub(r'([,(])\s*(?:locator|selector|text|value)\s*=\s*', r'\1', code_str)

    # 2. Convert common JS camelCase methods to Playwright Python snake_case
    replacements = {
        r'page\.url\(\)': 'page.url',  # Property fix
        r'\.waitForURL\(': '.wait_for_url(',
        r'\.waitForSelector\(': '.wait_for_selector(',
        r'\.waitForTimeout\(': '.wait_for_timeout(',
        r'\.waitForFunction\(': '.wait_for_function(',
        r'\.text\(\)': '.inner_text()',  # Fix common text() call on locator
        r'\.text\b(?!\()': '.inner_text()',  # Fix .text property access on locator
    }
    for pattern, replacement in replacements.items():
        code_str = re.sub(pattern, replacement, code_str)

    lines = code_str.split("\n")
    kept_lines_with_indent = []
    
    # 3. Scrub structural boilerplate and commented lines that break execution scope
    blacklisted_starts = (
        "import ", "from ", "asyncio.run", "async_playwright", "sync_playwright",
        "browser =", "context =", "page =", "async def ", "def ",
        "try:", "finally:", "except", "if __name__", "#",
        "with sync_playwright", "with async_playwright", "async with async_playwright",
        "browser.close", "context.close", "page.close", "playwright.stop",
        "run()", "main()", "await run()", "await main()"
    )
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            kept_lines_with_indent.append((0, ""))
            continue
            
        # Skip blacklisted keywords, imports, setup/teardown, and commented lines
        if any(stripped.startswith(bad) for bad in blacklisted_starts):
            continue
            
        indent = len(line) - len(line.lstrip())
        kept_lines_with_indent.append((indent, stripped))
        
    # Calculate minimum indentation of non-empty kept lines
    non_empty_indents = [indent for indent, stripped in kept_lines_with_indent if stripped]
    min_indent = min(non_empty_indents) if non_empty_indents else 0
    
    # Reconstruct lines with base indentation of 4 spaces
    aligned_lines = []
    for indent, stripped in kept_lines_with_indent:
        if not stripped:
            aligned_lines.append("")
        else:
            new_indent = 4 + max(0, indent - min_indent)
            aligned_lines.append(" " * new_indent + stripped)
            
    # Prepend 'await ' to Playwright async methods if they are not already awaited
    # List of Playwright methods that must be awaited
    async_methods = (
        "goto", "fill", "click", "screenshot", "title", "content",
        "wait_for_url", "wait_for_selector", "wait_for_timeout", "wait_for_load_state",
        "inner_text", "text_content", "all_inner_texts", "all_text_contents",
        "get_attribute", "is_visible", "is_hidden", "is_enabled", "is_checked",
        "is_disabled", "is_editable", "count", "select_option", "dispatch_event",
        "evaluate", "evaluate_handle", "hover", "focus", "press", "type",
        "reload", "go_back", "go_forward", "close", "all"
    )
    
    # Safe pattern using non-nested parenthesized wildcard search inside chained calls
    pattern = re.compile(
        r'\b([a-zA-Z_][a-zA-Z0-9_]*(?:\s*\.\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\([^()]*\))*\s*\.\s*(?:' +
        '|'.join(async_methods) +
        r')\s*\()'
    )
    
    final_lines = []
    for line in aligned_lines:
        if not line.strip():
            final_lines.append(line)
            continue
            
        # If the line already has 'await', leave it
        if "await" in line:
            final_lines.append(line)
            continue
            
        if pattern.search(line):
            new_line = pattern.sub(r'await \1', line)
            final_lines.append(new_line)
        else:
            final_lines.append(line)
            
    return "\n".join(final_lines) if final_lines else "    pass"


def _extract_selectors_from_srs(srs_content: str) -> list:
    """Extracts valid CSS selectors from the SRS document dynamically."""
    selectors = set()
    for line in srs_content.split('\n'):
        line = line.strip()
        if ':' in line and (line.startswith('-') or line.startswith('*') or any(c.isalnum() for c in line.split(':', 1)[0])):
            parts = line.split(':', 1)
            val = parts[1].strip()
            for token in val.split():
                if any(char in token for char in ('#', '.', '[')):
                    clean_token = token.strip("()',\"")
                    selectors.add(clean_token)
    return list(selectors)


def _resolve_selectors_dynamically(code_str: str, srs_content: str) -> str:
    """Fuzzy-matches LLM-generated selectors against valid selectors in the SRS."""
    valid_selectors = _extract_selectors_from_srs(srs_content)
    if not valid_selectors:
        return code_str
        
    str_pattern = re.compile(r'(["\'])([^"\']+)\1')
    
    def replace_selector(match):
        quote = match.group(1)
        val = match.group(2).strip()
        
        is_selector = any(c in val for c in ('#', '.', '[')) and not ' ' in val
        if is_selector and val not in valid_selectors:
            matches = difflib.get_close_matches(val, valid_selectors, n=1, cutoff=0.4)
            if matches:
                return f"{quote}{matches[0]}{quote}"
        return match.group(0)
        
    return str_pattern.sub(replace_selector, code_str)



async def execute_playwright_test(state: dict) -> dict:
    """Executes the dynamic Playwright script against a Chromium browser context."""
    target_url = state.get("target_url", "")
    ui_script = state.get("ui_script", "")
    srs_document = state.get("srs_document", "")
    output_dir = state.get("output_dir", "agent_outputs")
    
    os.makedirs(output_dir, exist_ok=True)
    screenshot_path = os.path.join(output_dir, "agent_4_failure_screenshot.png")
    error_log_path = os.path.join(output_dir, "agent_4_error_log.json")
    
    page_console_logs = []
    screenshot_captured = False
    
    try:
        async with async_playwright() as p:
            # Launch Chromium Engine
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(base_url=target_url)
            
            # Set default locator timeout to 5000ms (5s) for fast failure loops
            context.set_default_timeout(5000)
            
            page = await context.new_page()
            
            # Catch browser console errors
            page.on(
                "console", 
                lambda msg: page_console_logs.append(f"[{msg.type.upper()}] {msg.text}") 
                if msg.type == "error" else None
            )
            
            try:
                # Navigation
                response = await page.goto(target_url, timeout=15000, wait_until="load")
                status_code = response.status if response else 0
                
                if status_code < 200 or status_code >= 400:
                    raise Exception(f"HTTP Navigation Error: Target URL returned status code {status_code}")

                # Dynamic Execution
                exec_scope = {
                    "page": page,
                    "browser": browser,
                    "context": context,
                    "target_url": target_url
                }
                
                indented_body = _clean_and_indent_script(ui_script)
                indented_body = _resolve_selectors_dynamically(indented_body, srs_document)
                wrapped_code = f"async def __run_generated_test(page, target_url):\n{indented_body}"

                exec(wrapped_code, exec_scope)
                await exec_scope["__run_generated_test"](page, target_url)

                title = await page.title()
                await browser.close()
                
                return {
                    "execution_result": {
                        "status": "PASSED",
                        "http_status": status_code,
                        "page_title": title,
                        "target_url": target_url,
                        "console_errors": page_console_logs
                    }
                }
            except Exception as e:
                # Capture screenshot before the Playwright context manager exits and closes the connection
                try:
                    if 'page' in locals() and not page.is_closed():
                        await page.screenshot(path=screenshot_path, full_page=True)
                        screenshot_captured = True
                except Exception:
                    pass
                raise e
                
    except Exception as e:
        error_type = (
            "TimeoutError"
            if isinstance(e, PlaywrightTimeoutError)
            else ("AssertionError" if isinstance(e, AssertionError) else type(e).__name__)
        )
        
        # Extract the exact line of code that failed from traceback
        failed_line = ""
        try:
            tb = e.__traceback__
            while tb:
                if tb.tb_frame.f_code.co_filename == "<string>":
                    line_num = tb.tb_lineno
                    if 'wrapped_code' in locals():
                        lines = wrapped_code.split('\n')
                        if 1 <= line_num <= len(lines):
                            failed_line = lines[line_num - 1].strip()
                    break
                tb = tb.tb_next
        except Exception:
            pass
            
        failure_msg = str(e)
        if isinstance(e, AssertionError):
            failure_msg = f"Assertion failed: {failed_line}" if failed_line else "Assertion failed"
        elif failed_line:
            msg = str(e)
            failure_msg = f"{type(e).__name__}: {msg} (at: {failed_line})" if msg else f"{type(e).__name__} (at: {failed_line})"
            
        error_data = {
            "error_type": error_type,
            "failure_reason": failure_msg,
            "traceback": traceback.format_exc(),
            "target_url": target_url,
            "console_errors": page_console_logs,
            "failed_script_code": ui_script,
            "screenshot_saved": screenshot_path if screenshot_captured else None
        }

        with open(error_log_path, "w", encoding="utf-8") as f:
            json.dump(error_data, f, indent=4)

        return {
            "execution_result": {
                "status": "FAILED",
                "error_type": error_type,
                "error_message": failure_msg,
                "error_file": error_log_path,
                "screenshot": screenshot_path if screenshot_captured else None
            }
        }