import asyncio
import os
import shutil
from playwright.async_api import async_playwright

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOTS_DIR = os.path.join(WORKSPACE_DIR, "screenshots")
ARTIFACTS_DIR = r"C:\Users\Boomika\.gemini\antigravity\brain\0fd2cefc-2b15-4b80-b082-19c332e736cb"

os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

async def capture_all_figures():
    print("[*] Launching Chromium browser with Playwright...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use 1600x1000 viewport with device_scale_factor=2 for ultra-crisp report figures
        context = await browser.new_context(
            viewport={"width": 1600, "height": 1000},
            device_scale_factor=2,
            color_scheme="dark",
        )
        page = await context.new_page()

        # -------------------------------------------------------------
        # Figure 6.1: Login and User Authentication Interface
        # -------------------------------------------------------------
        print("\n[+] Capturing Figure 6.1: Login and User Authentication Interface...")
        await page.goto("http://localhost:5173/login", wait_until="networkidle")
        await page.wait_for_selector(".auth-form", state="visible")
        
        # Click the Admin tab on login
        admin_tab = await page.query_selector('button[role="tab"]:has-text("Admin")')
        if admin_tab:
            await admin_tab.click()
            await asyncio.sleep(0.3)

        # Pre-fill email and password
        await page.fill('input[type="email"]', "admin@example.com")
        await page.fill('input[type="password"]', "Admin@123")
        await page.check('input[type="checkbox"]')
        await asyncio.sleep(0.5)

        fig_6_1_path = os.path.join(SCREENSHOTS_DIR, "Figure_6_1_Login_and_Authentication_Interface.png")
        await page.screenshot(path=fig_6_1_path, full_page=False)
        print(f"    [OK] Saved Figure 6.1 to: {fig_6_1_path}")

        # Now submit login form
        await page.click('button[type="submit"]')
        await asyncio.sleep(1.5)

        # -------------------------------------------------------------
        # Figure 6.2: Project Dashboard and SRS Upload Interface
        # -------------------------------------------------------------
        print("\n[+] Capturing Figure 6.2: Project Dashboard and SRS Upload Interface...")
        await page.goto("http://localhost:5173/dashboard", wait_until="networkidle")
        await asyncio.sleep(1.2)
        fig_6_2_dash_path = os.path.join(SCREENSHOTS_DIR, "Figure_6_2_Project_Dashboard_Overview.png")
        await page.screenshot(path=fig_6_2_dash_path, full_page=False)
        print(f"    [OK] Saved Dashboard overview to: {fig_6_2_dash_path}")

        # Navigate to New Project creation / SRS Upload interface
        await page.goto("http://localhost:5173/projects/new", wait_until="networkidle")
        await page.wait_for_selector('input[type="text"]', state="visible")
        
        text_inputs = await page.query_selector_all('input[type="text"]')
        if len(text_inputs) >= 2:
            await text_inputs[0].fill("SauceDemo E-Commerce Smoke Test Suite")
            await text_inputs[1].fill("https://www.saucedemo.com")
        elif len(text_inputs) == 1:
            await text_inputs[0].fill("SauceDemo E-Commerce Smoke Test Suite")

        # Load real SRS markdown from srs-document.txt
        srs_file_path = os.path.join(WORKSPACE_DIR, "srs-document.txt")
        if os.path.exists(srs_file_path):
            with open(srs_file_path, "r", encoding="utf-8") as f:
                srs_content = f.read()
            textarea = await page.query_selector("textarea")
            if textarea:
                await textarea.fill(srs_content)

        await asyncio.sleep(1)
        fig_6_2_path = os.path.join(SCREENSHOTS_DIR, "Figure_6_2_Project_Dashboard_and_SRS_Upload_Interface.png")
        await page.screenshot(path=fig_6_2_path, full_page=False)
        print(f"    [OK] Saved Figure 6.2 to: {fig_6_2_path}")

        # -------------------------------------------------------------
        # Figure 6.3: Automated Test Case Generation and Test Planning Interface
        # -------------------------------------------------------------
        print("\n[+] Capturing Figure 6.3: Automated Test Case Generation and Test Planning Interface...")
        await page.goto("http://localhost:5173/run-monitor?tab=test-cases", wait_until="networkidle")
        await asyncio.sleep(1.5)
        fig_6_3_path = os.path.join(SCREENSHOTS_DIR, "Figure_6_3_Automated_Test_Case_Generation_and_Planning_Interface.png")
        await page.screenshot(path=fig_6_3_path, full_page=False)
        print(f"    [OK] Saved Figure 6.3 to: {fig_6_3_path}")

        # -------------------------------------------------------------
        # Figure 6.4: Test Execution Monitoring and Root Cause Analysis Interface
        # -------------------------------------------------------------
        print("\n[+] Capturing Figure 6.4: Test Execution Monitoring and Root Cause Analysis Interface...")
        # A: Live Execution Monitoring with stage progression and terminal logs
        await page.goto("http://localhost:5173/run-monitor?tab=terminal", wait_until="networkidle")
        await asyncio.sleep(1.5)
        fig_6_4_path = os.path.join(SCREENSHOTS_DIR, "Figure_6_4_Test_Execution_Monitoring_and_RCA_Interface.png")
        await page.screenshot(path=fig_6_4_path, full_page=False)
        print(f"    [OK] Saved Figure 6.4 (Monitoring) to: {fig_6_4_path}")

        # B: Root Cause Analysis & Self-Healing Diagnoses View
        await page.goto("http://localhost:5173/run-monitor?tab=rca", wait_until="networkidle")
        await asyncio.sleep(1)
        fig_6_4_rca_path = os.path.join(SCREENSHOTS_DIR, "Figure_6_4_Root_Cause_Analysis_Detail_View.png")
        await page.screenshot(path=fig_6_4_rca_path, full_page=False)
        print(f"    [OK] Saved Figure 6.4 (RCA Detail) to: {fig_6_4_rca_path}")

        # -------------------------------------------------------------
        # Figure 6.5: Test Results, Security Findings, and Generated Reports Interface
        # -------------------------------------------------------------
        print("\n[+] Capturing Figure 6.5: Test Results, Security Findings, and Generated Reports Interface...")
        await page.goto("http://localhost:5173/success", wait_until="networkidle")
        await asyncio.sleep(1.5)
        fig_6_5_path = os.path.join(SCREENSHOTS_DIR, "Figure_6_5_Test_Results_Security_Findings_and_Reports_Interface.png")
        await page.screenshot(path=fig_6_5_path, full_page=True)
        print(f"    [OK] Saved Figure 6.5 to: {fig_6_5_path}")

        await browser.close()
        print("\n[*] All browser captures completed successfully!")

    # Copy all generated screenshots to ARTIFACTS_DIR for direct viewing
    for fname in os.listdir(SCREENSHOTS_DIR):
        if fname.endswith(".png"):
            src_file = os.path.join(SCREENSHOTS_DIR, fname)
            dst_file = os.path.join(ARTIFACTS_DIR, fname)
            shutil.copy2(src_file, dst_file)
            print(f"    [Copied] {fname} -> artifacts directory")

if __name__ == "__main__":
    asyncio.run(capture_all_figures())
