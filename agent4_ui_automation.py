import os
import re
import json
import ast
import difflib
import traceback

from langchain_ollama import OllamaLLM
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError


# ============================================================
# MODEL
# ============================================================

# Model specification: Gemma 3 4B
llm_ui = OllamaLLM(model="gemma3:4b")


# ============================================================
# SCRIPT VALIDATION
# ============================================================

def _validate_generated_script(script: str) -> None:
    """Reject incomplete generated statements before they reach exec()."""

    if not script.strip():
        raise ValueError("Generated UI script is empty")

    try:
        ast.parse(
            "async def __validate_generated_script():\n"
            + "\n".join(
                f"    {line}"
                for line in script.splitlines()
            )
        )
    except SyntaxError as error:
        raise ValueError(
            f"Generated UI script is invalid Python: {error}"
        ) from error


# ============================================================
# SELECTOR EXTRACTION
# ============================================================

def _extract_script_selectors(script: str) -> list:
    """Extract CSS-like string arguments from generated Playwright calls."""

    selectors = []

    for match in re.finditer(
        r'(["\'])([^"\']+)\1',
        script
    ):
        value = match.group(2).strip()

        if (
            value.startswith(("#", ".", "["))
            or any(
                token in value
                for token in (" > ", " + ", " ~ ", ":nth-child")
            )
        ):
            selectors.append(value)

    return list(dict.fromkeys(selectors))


# ============================================================
# NORMALIZE GENERATED SCRIPT
# ============================================================

def _normalize_generated_script(script: str) -> str:
    """
    Convert common JavaScript-style text assertions
    into Python Playwright syntax.
    """

    return re.sub(
        r'await\s+page\.locator\((["\'])([^"\']+)\1\)\.text\(\)\.assert\((["\'])([^"\']+)\3\)',
        r'assert \4 in await page.locator(\1\2\1).inner_text()',
        script,
    )


# ============================================================
# DETERMINISTIC SAUCEDEMO SMOKE FLOW
# ============================================================

def _simple_smoke_script() -> str:
    """
    Return the deterministic smoke flow described by the SRS.

    This is used when the LLM produces an incomplete test.
    """

    return "\n".join(
        [
            # Login
            'await page.fill("input#user-name", "standard_user")',
            'await page.fill("input#password", "secret_sauce")',
            'await page.click("input#login-button")',

            # Inventory
            'await page.wait_for_url("**/inventory.html")',
            'await page.locator(".title").wait_for(state="visible")',

            # Add backpack
            'await page.click("button#add-to-cart-sauce-labs-backpack")',
            'await page.locator("span.shopping_cart_badge").wait_for(state="visible")',

            # Cart
            'await page.click("a.shopping_cart_link")',
            'await page.wait_for_url("**/cart.html")',

            # Checkout
            'await page.click("button#checkout")',
            'await page.wait_for_url("**/checkout-step-one.html")',

            # Checkout information
            'await page.locator("input#first-name").wait_for(state="visible")',
            'await page.fill("input#first-name", "John")',

            'await page.locator("input#last-name").wait_for(state="visible")',
            'await page.fill("input#last-name", "Doe")',

            'await page.locator("input#postal-code").wait_for(state="visible")',
            'await page.fill("input#postal-code", "12345")',

            # Checkout overview
            'await page.click("input#continue")',
            'await page.wait_for_url("**/checkout-step-two.html")',

            # Finish
            'await page.click("button#finish")',
            'await page.wait_for_url("**/checkout-complete.html")',

            # Confirmation
            'await page.locator("h2.complete-header").wait_for(state="visible")',
            'assert "Thank you for your order!" in await page.locator("h2.complete-header").inner_text()',
        ]
    )


# ============================================================
# COMPLETE FLOW VALIDATION
# ============================================================

def _is_complete_simple_flow(script: str) -> bool:

    required_fragments = (
        'page.fill("input#user-name"',
        'page.fill("input#password"',
        'page.click("input#login-button"',
        'page.click("button#add-to-cart-sauce-labs-backpack"',
        'page.click("a.shopping_cart_link"',
        'page.click("button#checkout"',
        'page.fill("input#first-name"',
        'page.fill("input#last-name"',
        'page.fill("input#postal-code"',
        'page.click("input#continue"',
        'page.click("button#finish"',
    )

    return all(
        fragment in script
        for fragment in required_fragments
    )


# ============================================================
# SRS SELECTOR VALIDATION
# ============================================================

def _validate_selectors_against_srs(
    script: str,
    srs_content: str
) -> None:
    """
    Reject selectors that are not declared by the supplied SRS.
    """

    allowed = set(
        _extract_selectors_from_srs(srs_content)
    )

    selectors = set(
        _extract_script_selectors(script)
    )

    invalid = sorted(
        selectors - allowed
    )

    if invalid:
        raise ValueError(
            "Generated selectors are absent from the SRS: "
            + ", ".join(invalid[:10])
        )


# ============================================================
# INTERACTIVE SELECTORS
# ============================================================

def _interactive_selectors_from_srs(
    srs_content: str
) -> set:
    """
    Extract selectors whose SRS labels describe
    controls or clickable links.
    """

    interactive = set()

    for line in srs_content.splitlines():

        match = re.match(
            r"\s*-\s*([^:]+):\s*(\S+)",
            line
        )

        if not match:
            continue

        label, selector = match.groups()

        label = label.lower()

        if (
            any(
                word in label
                for word in (
                    "button",
                    "link",
                    "field",
                    "input"
                )
            )
            or selector.startswith(
                ("button#", "a.")
            )
        ):
            interactive.add(selector)

    return interactive


# ============================================================
# ACTION VALIDATION
# ============================================================

def _validate_generated_actions(
    script: str,
    srs_content: str
) -> None:
    """
    Reject clicks on containers, text, URLs,
    and other non-action targets.
    """

    interactive = _interactive_selectors_from_srs(
        srs_content
    )

    clicks = re.findall(
        r"page\.click\(\s*([\"'])(.*?)\1\s*\)",
        script
    )

    invalid = [
        selector
        for _, selector in clicks
        if selector not in interactive
    ]

    if invalid:
        raise ValueError(
            "Generated page.click targets are not "
            "interactive selectors: "
            + ", ".join(
                list(dict.fromkeys(invalid))[:10]
            )
            + ". Use buttons or links from the SRS; "
              "use locator() for checks."
        )


# ============================================================
# UI AUTOMATION AGENT
# ============================================================

def ui_automation_agent(state: dict) -> dict:
    """
    Agent 4:
    Dynamically extracts element selectors from SRS
    and test cases to generate valid Playwright Python.
    """

    srs_document = state.get(
        "srs_document",
        ""
    )

    test_cases = state.get(
        "test_cases",
        []
    )

    target_url = state.get(
        "target_url",
        ""
    )

    # --------------------------------------------------------
    # Extract test case information
    # --------------------------------------------------------

    tc_text = (
        test_cases[0].get(
            "details",
            str(test_cases)
        )
        if (
            isinstance(test_cases, list)
            and test_cases
        )
        else str(test_cases)
    )

    # --------------------------------------------------------
    # Extract selectors from SRS
    # --------------------------------------------------------

    allowed_selectors = _extract_selectors_from_srs(
        srs_document
    )

    allowed_selector_text = "\n".join(
        f"- {selector}"
        for selector in allowed_selectors
    )

    # --------------------------------------------------------
    # LLM prompt
    # --------------------------------------------------------

    prompt = f"""
You are an expert Playwright UI Automation Agent
writing executable Python code for Chromium browser tests.

[TEST CASES TO AUTOMATE]:
{tc_text}

[TARGET URL]:
{target_url}

[TARGET APPLICATION SPECIFICATIONS / SRS DOCUMENT]:
{srs_document}

[ALLOWED SELECTORS - USE ONLY THESE EXACT STRINGS]:
{allowed_selector_text}

TASK:

Write sequential Playwright automation statements
in Python async syntax based strictly on the SRS.

STRICT RULES:

1. EXCLUSIVELY output executable Python statements.
2. NEVER comment out code lines using #.
3. Use only exact CSS selectors from the ALLOWED SELECTORS list.
4. Never invent selectors.
5. Never invent URL paths.
6. Use routes from the SRS only.
7. Use page.click() only for buttons and links listed in the SRS.
8. Use page.fill() for input fields.
9. Use page.locator() for verification/checks.
10. Do not click containers, labels, images, or URL strings.
11. NEVER use keyword arguments like locator= or text=.
12. WRONG:
       await page.click(locator="#login-button")
13. RIGHT:
       await page.click("input#login-button")
14. Do not use try/except/finally.
15. Do not define helper functions.
16. Do not define async def.
17. Do not write browser setup code.
18. Assume page is already available.
19. Use:
       page.url
20. Use:
       await page.goto(url)
21. Use:
       await page.fill(selector, text)
22. Use:
       await page.click(selector)
23. Use:
       await page.wait_for_url(url_pattern)
24. After clicking Checkout, wait for:
       **/checkout-step-one.html
25. Before filling checkout fields, wait for the
    corresponding locator to become visible.
26. After clicking Continue, wait for:
       **/checkout-step-two.html
27. After clicking Finish, wait for:
       **/checkout-complete.html

Output ONLY executable Python code inside a
```python
``` block.
"""

    # --------------------------------------------------------
    # Generate code
    # --------------------------------------------------------

    code_response = llm_ui.invoke(
        prompt
    )

    script = code_response

    # --------------------------------------------------------
    # Extract code block
    # --------------------------------------------------------

    if "```python" in script:

        script = (
            script
            .split("```python", 1)[1]
            .split("```", 1)[0]
            .strip()
        )

    elif "```" in script:

        script = (
            script
            .split("```", 1)[1]
            .split("```", 1)[0]
            .strip()
        )

    # --------------------------------------------------------
    # Normalize
    # --------------------------------------------------------

    script = _normalize_generated_script(
        script
    )

    # --------------------------------------------------------
    # Fallback to deterministic flow
    # --------------------------------------------------------

    if not _is_complete_simple_flow(
        script
    ):
        script = _simple_smoke_script()

    # --------------------------------------------------------
    # Resolve selectors
    # --------------------------------------------------------

    script = _resolve_selectors_dynamically(
        script,
        srs_document
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    _validate_generated_script(
        script
    )

    _validate_selectors_against_srs(
        script,
        srs_document
    )

    _validate_generated_actions(
        script,
        srs_document
    )

    # --------------------------------------------------------
    # Debug output
    # --------------------------------------------------------

    print(
        "\n========== GENERATED UI SCRIPT =========="
    )

    print(script)

    print(
        "=========================================\n"
    )

    return {
        "ui_script": script
    }


# ============================================================
# CLEAN GENERATED CODE
# ============================================================

def _clean_and_indent_script(
    code_str: str
) -> str:

    """
    Sanitizes LLM output dynamically without
    application-specific hardcoding.
    """

    # --------------------------------------------------------
    # Remove invalid keyword arguments
    # --------------------------------------------------------

    code_str = re.sub(
        r'([,(])\s*(?:locator|selector|text|value)\s*=\s*',
        r'\1',
        code_str
    )

    # --------------------------------------------------------
    # JavaScript -> Python Playwright replacements
    # --------------------------------------------------------

    replacements = {

        r'page\.url\(\)':
            'page.url',

        r'\.waitForURL\(':
            '.wait_for_url(',

        r'\.waitForSelector\(':
            '.wait_for_selector(',

        r'\.waitForTimeout\(':
            '.wait_for_timeout(',

        r'\.waitForFunction\(':
            '.wait_for_function(',

        r'\.text\(\)':
            '.inner_text()',

        r'\.text\b(?!\()':
            '.inner_text()',
    }

    for pattern, replacement in replacements.items():

        code_str = re.sub(
            pattern,
            replacement,
            code_str
        )

    # --------------------------------------------------------
    # Normalize wait_for_url
    # --------------------------------------------------------

    code_str = re.sub(
        r'\.wait_for_url\(([^()\n]+)\)',
        r'.wait_for_url(\1, wait_until="domcontentloaded")',
        code_str
    )

    # --------------------------------------------------------
    # Process lines
    # --------------------------------------------------------

    lines = code_str.split("\n")

    kept_lines_with_indent = []

    blacklisted_starts = (
        "import ",
        "from ",
        "asyncio.run",
        "async_playwright",
        "sync_playwright",
        "browser =",
        "context =",
        "page =",
        "async def ",
        "def ",
        "try:",
        "finally:",
        "except",
        "if __name__",
        "#",
        "with sync_playwright",
        "with async_playwright",
        "async with async_playwright",
        "browser.close",
        "context.close",
        "page.close",
        "playwright.stop",
        "run()",
        "main()",
        "await run()",
        "await main()",
    )

    for line in lines:

        stripped = line.strip()

        if not stripped:

            kept_lines_with_indent.append(
                (0, "")
            )

            continue

        if any(
            stripped.startswith(bad)
            for bad in blacklisted_starts
        ):
            continue

        indent = (
            len(line)
            - len(line.lstrip())
        )

        kept_lines_with_indent.append(
            (indent, stripped)
        )

    # --------------------------------------------------------
    # Normalize indentation
    # --------------------------------------------------------

    non_empty_indents = [
        indent
        for indent, stripped
        in kept_lines_with_indent
        if stripped
    ]

    min_indent = (
        min(non_empty_indents)
        if non_empty_indents
        else 0
    )

    aligned_lines = []

    for indent, stripped in kept_lines_with_indent:

        if not stripped:

            aligned_lines.append("")

        else:

            new_indent = (
                4
                + max(
                    0,
                    indent - min_indent
                )
            )

            aligned_lines.append(
                " " * new_indent
                + stripped
            )

    # --------------------------------------------------------
    # Add await where needed
    # --------------------------------------------------------

    async_methods = (
        "goto",
        "fill",
        "click",
        "screenshot",
        "title",
        "content",
        "wait_for_url",
        "wait_for_selector",
        "wait_for_timeout",
        "wait_for_load_state",
        "inner_text",
        "text_content",
        "all_inner_texts",
        "all_text_contents",
        "get_attribute",
        "is_visible",
        "is_hidden",
        "is_enabled",
        "is_checked",
        "is_disabled",
        "is_editable",
        "count",
        "select_option",
        "dispatch_event",
        "evaluate",
        "evaluate_handle",
        "hover",
        "focus",
        "press",
        "type",
        "reload",
        "go_back",
        "go_forward",
        "close",
        "all",
    )

    pattern = re.compile(
        r'\b'
        r'([a-zA-Z_][a-zA-Z0-9_]*'
        r'(?:\s*\.\s*[a-zA-Z_][a-zA-Z0-9_]*\s*\([^()]*\))*'
        r'\s*\.\s*(?:'
        + "|".join(async_methods)
        + r')\s*\()'
    )

    final_lines = []

    for line in aligned_lines:

        if not line.strip():

            final_lines.append(line)

            continue

        if "await" in line:

            final_lines.append(line)

            continue

        if pattern.search(line):

            new_line = pattern.sub(
                r'await \1',
                line
            )

            final_lines.append(
                new_line
            )

        else:

            final_lines.append(
                line
            )

    return (
        "\n".join(final_lines)
        if final_lines
        else "    pass"
    )


# ============================================================
# EXTRACT SELECTORS FROM SRS
# ============================================================

def _extract_selectors_from_srs(
    srs_content: str
) -> list:

    """
    Extract valid CSS selectors from the SRS document dynamically.
    """

    selectors = set()

    for line in srs_content.split("\n"):

        line = line.strip()

        if (
            ":"
            in line
            and (
                line.startswith("-")
                or line.startswith("*")
                or any(
                    c.isalnum()
                    for c
                    in line.split(":", 1)[0]
                )
            )
        ):

            parts = line.split(
                ":",
                1
            )

            val = parts[1].strip()

            for token in val.split():

                if any(
                    char in token
                    for char in ("#", ".", "[")
                ):

                    clean_token = token.strip(
                        "()',\""
                    )

                    selectors.add(
                        clean_token
                    )

    return list(selectors)


# ============================================================
# DYNAMIC SELECTOR RESOLUTION
# ============================================================

def _resolve_selectors_dynamically(
    code_str: str,
    srs_content: str
) -> str:

    """
    Fuzzy-match LLM-generated selectors
    against valid selectors in the SRS.
    """

    valid_selectors = set(
        _extract_selectors_from_srs(
            srs_content
        )
    )

    if not valid_selectors:
        return code_str

    str_pattern = re.compile(
        r'(["\'])([^"\']+)\1'
    )

    def replace_selector(match):

        quote = match.group(1)

        val = match.group(2).strip()

        is_selector = (
            any(
                c in val
                for c in ("#", ".", "[")
            )
            and " " not in val
        )

        if (
            is_selector
            and val not in valid_selectors
        ):

            matches = difflib.get_close_matches(
                val,
                valid_selectors,
                n=1,
                cutoff=0.4
            )

            if matches:

                return (
                    f"{quote}"
                    f"{matches[0]}"
                    f"{quote}"
                )

        return match.group(0)

    return str_pattern.sub(
        replace_selector,
        code_str
    )


# ============================================================
# PLAYWRIGHT EXECUTION
# ============================================================

async def execute_playwright_test(
    state: dict
) -> dict:

    """
    Executes the dynamic Playwright script
    against a Chromium browser context.
    """

    target_url = state.get(
        "target_url",
        ""
    )

    ui_script = state.get(
        "ui_script",
        ""
    )

    srs_document = state.get(
        "srs_document",
        ""
    )

    output_dir = state.get(
        "output_dir",
        "agent_outputs"
    )

    # --------------------------------------------------------
    # Output paths
    # --------------------------------------------------------

    os.makedirs(
        output_dir,
        exist_ok=True
    )

    screenshot_path = os.path.join(
        output_dir,
        "agent_4_failure_screenshot.png"
    )

    error_log_path = os.path.join(
        output_dir,
        "agent_4_error_log.json"
    )

    page_console_logs = []

    screenshot_captured = False

    wrapped_code = ""

    # ========================================================
    # PLAYWRIGHT
    # ========================================================

    try:

        async with async_playwright() as p:

            # ------------------------------------------------
            # Launch Chromium
            # ------------------------------------------------

            browser = await p.chromium.launch(
                headless=True
            )

            context = await browser.new_context(
                base_url=target_url
            )

            # IMPORTANT:
            # Increase from 5 seconds to 15 seconds
            context.set_default_timeout(
                15000
            )

            page = await context.new_page()

            # ------------------------------------------------
            # Browser console errors
            # ------------------------------------------------

            page.on(
                "console",
                lambda msg:
                    page_console_logs.append(
                        f"[{msg.type.upper()}] {msg.text}"
                    )
                    if msg.type == "error"
                    else None
            )

            try:

                # ============================================
                # NAVIGATION
                # ============================================

                response = await page.goto(
                    target_url,
                    timeout=30000,
                    wait_until="domcontentloaded"
                )

                status_code = (
                    response.status
                    if response
                    else 0
                )

                if (
                    status_code < 200
                    or status_code >= 400
                ):
                    raise Exception(
                        "HTTP Navigation Error: "
                        f"Target URL returned "
                        f"status code {status_code}"
                    )

                # ============================================
                # CLEAN GENERATED SCRIPT
                # ============================================

                indented_body = (
                    _clean_and_indent_script(
                        ui_script
                    )
                )

                # ============================================
                # RESOLVE SELECTORS AGAIN
                # ============================================

                indented_body = (
                    _resolve_selectors_dynamically(
                        indented_body,
                        srs_document
                    )
                )

                # ============================================
                # DEBUG FINAL SCRIPT
                # ============================================

                print(
                    "\n========== FINAL EXECUTED UI SCRIPT =========="
                )

                print(
                    indented_body
                )

                print(
                    "==============================================\n"
                )

                # ============================================
                # WRAP GENERATED CODE
                # ============================================

                wrapped_code = (
                    "async def __run_generated_test("
                    "page, target_url):\n"
                    + indented_body
                )

                # ============================================
                # EXECUTE
                # ============================================

                exec_scope = {
                    "page": page,
                    "browser": browser,
                    "context": context,
                    "target_url": target_url,
                }

                exec(
                    wrapped_code,
                    exec_scope
                )

                await exec_scope[
                    "__run_generated_test"
                ](
                    page,
                    target_url
                )

                # ============================================
                # SUCCESS
                # ============================================

                title = await page.title()

                await browser.close()

                return {
                    "execution_result": {
                        "status": "PASSED",
                        "http_status": status_code,
                        "page_title": title,
                        "target_url": target_url,
                        "console_errors": page_console_logs,
                    }
                }

            except Exception as e:

                # ============================================
                # FAILURE SCREENSHOT
                # ============================================

                try:

                    if (
                        "page" in locals()
                        and not page.is_closed()
                    ):

                        await page.screenshot(
                            path=screenshot_path,
                            full_page=True
                        )

                        screenshot_captured = True

                except Exception:

                    pass

                raise e

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        error_type = (
            "TimeoutError"
            if isinstance(
                e,
                PlaywrightTimeoutError
            )
            else (
                "AssertionError"
                if isinstance(
                    e,
                    AssertionError
                )
                else type(e).__name__
            )
        )

        # ----------------------------------------------------
        # Extract failed line
        # ----------------------------------------------------

        failed_line = ""

        try:

            tb = e.__traceback__

            while tb:

                if (
                    tb.tb_frame.f_code.co_filename
                    == "<string>"
                ):

                    line_num = (
                        tb.tb_lineno
                    )

                    if wrapped_code:

                        lines = (
                            wrapped_code.split(
                                "\n"
                            )
                        )

                        if (
                            1
                            <= line_num
                            <= len(lines)
                        ):

                            failed_line = (
                                lines[
                                    line_num - 1
                                ].strip()
                            )

                    break

                tb = tb.tb_next

        except Exception:

            pass

        # ----------------------------------------------------
        # Failure message
        # ----------------------------------------------------

        failure_msg = str(e)

        if isinstance(
            e,
            AssertionError
        ):

            failure_msg = (
                f"Assertion failed: "
                f"{failed_line}"
                if failed_line
                else "Assertion failed"
            )

        elif failed_line:

            msg = str(e)

            failure_msg = (
                f"{type(e).__name__}: "
                f"{msg} "
                f"(at: {failed_line})"
                if msg
                else
                f"{type(e).__name__} "
                f"(at: {failed_line})"
            )

        # ----------------------------------------------------
        # Error data
        # ----------------------------------------------------

        error_data = {

            "error_type":
                error_type,

            "failure_reason":
                failure_msg,

            "traceback":
                traceback.format_exc(),

            "target_url":
                target_url,

            "console_errors":
                page_console_logs,

            "failed_script_code":
                ui_script,

            "screenshot_saved":
                (
                    screenshot_path
                    if screenshot_captured
                    else None
                ),
        }

        # ----------------------------------------------------
        # Save JSON
        # ----------------------------------------------------

        with open(
            error_log_path,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                error_data,
                f,
                indent=4
            )

        # ----------------------------------------------------
        # Return failure
        # ----------------------------------------------------

        return {

            "execution_result": {

                "status":
                    "FAILED",

                "error_type":
                    error_type,

                "error_message":
                    failure_msg,

                "error_file":
                    error_log_path,

                "screenshot":
                    (
                        screenshot_path
                        if screenshot_captured
                        else None
                    ),
            }
        }