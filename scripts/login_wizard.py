import os
import asyncio
from playwright.async_api import async_playwright

# V4: Persistent Profile Path (Industrial Standard)
USER_DATA_DIR = os.path.expanduser("~/.notebooklm-mcp/chrome_profile")

async def login_wizard():
    print("🧙‍♂️ NotebookLM Login Wizard (Persistent Mode) Initialized...")
    print(f"📂 Profile Location: {USER_DATA_DIR}")
    print("------------------------------------------------")
    print("🚀 Launching Chrome... Please login to your Google Account.")
    
    # Ensure dir exists
    os.makedirs(USER_DATA_DIR, exist_ok=True)

    async with async_playwright() as p:
        # Launch with HEADFUL = True so user can interact
        # Using launch_persistent_context to save the session to disk
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = await browser.new_page() if not browser.pages else browser.pages[0]
        
        try:
            await page.goto("https://notebooklm.google.com/")
        except Exception as e:
            print(f"❌ Navigation failed: {e}")

        print("\nDO NOT CLOSE THE BROWSER YET!")
        print("👉 Please log in manually in the opened window.")
        print("👉 Once you see your NotebookLM dashboard, press Enter here in the terminal.")
        
        input("Press Enter to save profile and finish...")
        
        # In persistent mode, closing the context saves the state to the user_data_dir
        await browser.close()
            
        print(f"✅ Profile saved to: {USER_DATA_DIR}")
        print("🎉 You are all set! The pipeline will now use this persistent session.")

if __name__ == "__main__":
    asyncio.run(login_wizard())
