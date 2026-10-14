import asyncio
from playwright.async_api import async_playwright
import urllib.request, json

async def check_dash():
    api_url = 'http://127.0.0.1:4000/api'
    login_body = json.dumps({'email': 'browser_test_user@example.com', 'password': 'Password@123'}).encode('utf-8')
    req = urllib.request.Request(f'{api_url}/auth/login', data=login_body, headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(req) as res:
        token = json.loads(res.read().decode())['token']

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto('http://localhost:5173/login', wait_until='networkidle')
        await page.evaluate(f"() => {{ localStorage.setItem('agentqa_token', '{token}'); }}")

        print("Navigating to http://localhost:5173/dashboard ...")
        await page.goto('http://localhost:5173/dashboard', wait_until='networkidle')
        stat_el = await page.wait_for_selector('.dash-stat', timeout=10000)
        print('Stat element found:', stat_el is not None)
        text = await page.inner_text('.dashboard')
        print('Dashboard text snippet:\n', text[:300])
        await browser.close()

if __name__ == '__main__':
    asyncio.run(check_dash())
