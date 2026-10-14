import asyncio
from playwright.async_api import async_playwright
import urllib.request, json

async def test_ui_e2e():
    # 1. Create a clean user via API for testing
    api_url = "http://127.0.0.1:4000/api"
    reg_body = json.dumps({
        "fullName": "Browser Tester",
        "email": "browser_test_user@example.com",
        "password": "Password@123"
    }).encode("utf-8")
    
    token = None
    try:
        req = urllib.request.Request(f"{api_url}/auth/register", data=reg_body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode())
            token = data["token"]
            print("API registered test user.")
    except Exception as e:
        # User may already exist, login
        login_body = json.dumps({
            "email": "browser_test_user@example.com",
            "password": "Password@123"
        }).encode("utf-8")
        req = urllib.request.Request(f"{api_url}/auth/login", data=login_body, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req) as res:
            data = json.loads(res.read().decode())
            token = data["token"]
            print("API logged in test user.")

    # Create a project via API for this user so ProjectList and Dashboard have real data
    p_body = json.dumps({
        "name": "Live Browser Verification Project",
        "targetUrl": "https://browser-verify.example.com",
        "srsDocument": "# Browser Verification SRS\nTest end to end UI rendering."
    }).encode("utf-8")
    req_p = urllib.request.Request(f"{api_url}/projects", data=p_body, headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}, method="POST")
    with urllib.request.urlopen(req_p) as res:
        proj_data = json.loads(res.read().decode())
        print(f"API created test project: {proj_data['id']}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        # Set token in localStorage so auth context initializes as logged in
        await page.goto("http://localhost:5173/login", wait_until="networkidle")
        await page.evaluate(f"() => {{ localStorage.setItem('agentqa_token', '{token}'); }}")

        # Now navigate to dashboard
        print("Navigating to http://localhost:5173/dashboard ...")
        await page.goto("http://localhost:5173/", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        print("Dashboard Page URL:", page.url)
        content = await page.content()
        has_stats = "Total Projects" in content and "Active Runs" in content
        print(f"Dashboard rendered live stats cards: {has_stats}")

        # Navigate to Projects page
        print("Navigating to http://localhost:5173/projects ...")
        await page.goto("http://localhost:5173/projects", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        p_content = await page.content()
        has_project_card = "Live Browser Verification Project" in p_content
        print(f"Projects page rendered real MongoDB project: {has_project_card}")

        # Navigate to Project Creator
        print("Navigating to http://localhost:5173/projects/new ...")
        await page.goto("http://localhost:5173/projects/new", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        c_content = await page.content()
        has_creator_form = "Project Name" in c_content or "Target URL" in c_content or "SRS Document" in c_content
        print(f"Project creator rendered successfully: {has_creator_form}")

        # Clean up created project
        del_req = urllib.request.Request(f"{api_url}/projects/{proj_data['id']}", headers={"Authorization": f"Bearer {token}"}, method="DELETE")
        with urllib.request.urlopen(del_req) as res:
            print("Cleaned up test project:", json.loads(res.read().decode()))

        await browser.close()
        print("Browser end-to-end verification completed successfully.")

if __name__ == "__main__":
    asyncio.run(test_ui_e2e())
