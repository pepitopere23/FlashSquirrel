#!/usr/bin/env python3
import os
import json
import asyncio
import sys
from playwright.async_api import async_playwright

# Import load_cookies from the automator if possible, or redefine
AUTH_FILE = os.path.expanduser("~/.notebooklm-mcp/auth.json")

async def load_cookies():
    if not os.path.exists(AUTH_FILE): return None
    try:
        with open(AUTH_FILE, 'r') as f:
            data = json.load(f)
            cookies = []
            if isinstance(data, dict) and "cookies" in data:
                raw_cookies = data["cookies"]
                if isinstance(raw_cookies, list):
                    for c in raw_cookies:
                        cookies.append({"name": c.get("name"), "value": c.get("value"), "domain": c.get("domain", ".google.com"), "path": c.get("path", "/")})
                elif isinstance(raw_cookies, dict):
                    for name, value in raw_cookies.items():
                        cookies.append({"name": name, "value": value, "url": "https://notebooklm.google.com", "secure": True})
            return cookies
    except: return None

async def scan_notebooks():
    print("🔍 Scanning NotebookLM Dashboard for duplicates...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        cookies = await load_cookies()
        if cookies: await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto("https://notebooklm.google.com/")
        
        # Give it time to load the dashboard
        await asyncio.sleep(5)
        
        # Extract all notebook titles
        # Based on screenshots, notebooks are in cards.
        # We look for elements that look like notebook titles.
        notebooks = []
        # This selector is a bit fuzzy, we might need to refine it.
        # Usually they are in elements with specific classes or just text inside cards.
        try:
            # Look for all elements that might be titles
            elements = await page.query_selector_all(".notebook-card-title, mat-card-title, .title")
            if not elements:
                # Fallback to a broader search
                content = await page.content()
                # We'll just try to get all text from elements that look like cards
                cards = await page.query_selector_all("mat-card")
                for card in cards:
                    text = await card.inner_text()
                    title = text.split('\n')[0]
                    notebooks.append(title.strip())
            else:
                for el in elements:
                    title = await el.inner_text()
                    notebooks.append(title.strip())
        except Exception as e:
            print(f"⚠️ Error scanning: {e}")

        await browser.close()
        
        # Identify duplicates
        seen = {}
        duplicates = []
        for n in notebooks:
            if not n or n == "建立新的筆記本" or n == "New Notebook": continue
            if n in seen:
                seen[n] += 1
                duplicates.append(n)
            else:
                seen[n] = 1
        
        print(f"\n📊 Scan Complete: Found {len(notebooks)} notebooks.")
        if duplicates:
            print("\n⚠️ DUPLICATES DETECTED:")
            for d in set(duplicates):
                print(f"  - {d} (Count: {seen[d]})")
            print("\n💡 Suggestion: Please open NotebookLM in your browser and delete the redundant ones.")
        else:
            print("\n✅ No simple duplicates found (exact name matches).")

if __name__ == "__main__":
    asyncio.run(scan_notebooks())
