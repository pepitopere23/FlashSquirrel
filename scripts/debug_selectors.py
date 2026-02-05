
import os
import asyncio
from playwright.async_api import async_playwright

USER_DATA_DIR = os.path.expanduser("~/.notebooklm-mcp/chrome_profile")

async def debug_selectors():
    async with async_playwright() as p:
        print(f"🕵️ Loading profile from: {USER_DATA_DIR}")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False, # Visual to see what happens
        )
        page = await context.new_page() if not context.pages else context.pages[0]
        
        print("🌐 Navigating to NotebookLM...")
        await page.goto("https://notebooklm.google.com/")
        await asyncio.sleep(5)
        
        # Check Dashboard Selectors
        notebooks = await page.locator("mat-card").all()
        print(f"📊 Dashboard: Found {len(notebooks)} notebooks.")
        
        if len(notebooks) > 0:
            # Enter the first notebook to check title selector
            print("➡️ Entering first notebook to check Title Inputs...")
            await notebooks[0].click()
            await page.wait_for_selector("input", timeout=10000)
            await asyncio.sleep(3)
            
            # Dump all inputs
            inputs = await page.locator("input").all()
            print(f"🔍 Found {len(inputs)} inputs inside notebook.")
            for i, inp in enumerate(inputs):
                try:
                    aria = await inp.get_attribute("aria-label")
                    val = await inp.input_value()
                    ph = await inp.get_attribute("placeholder")
                    print(f"   [{i}] Input | aria-label: '{aria}' | value: '{val}' | placeholder: '{ph}'")
                except:
                    pass
        else:
            print("❌ No notebooks found to enter.")

        await context.close()

if __name__ == "__main__":
    asyncio.run(debug_selectors())
