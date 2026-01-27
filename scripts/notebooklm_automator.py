#!/usr/bin/env python3
"""
NotebookLM Automator
Uses Playwright to physically click "New Notebook" and upload files.
"""

import os
import json
import sys
import asyncio
from playwright.async_api import async_playwright

AUTH_FILE = os.path.expanduser("~/.notebooklm-mcp/auth.json")

async def load_cookies():
    if not os.path.exists(AUTH_FILE):
        print(f"⚠️ Auth file not found: {AUTH_FILE}")
        return None
    try:
        with open(AUTH_FILE, 'r') as f:
            data = json.load(f)
            cookies = []
            
            # Format 1: List of Dicts (Standard Playwright)
            if isinstance(data, dict) and "cookies" in data:
                raw_cookies = data["cookies"]
                
                if isinstance(raw_cookies, list):
                    for c in raw_cookies:
                        cookies.append({
                            "name": c.get("name"),
                            "value": c.get("value"),
                            "domain": c.get("domain", ".google.com"),
                            "path": c.get("path", "/")
                        })
                # Format 2: Key-Value Dict (The format found in user's file)
                elif isinstance(raw_cookies, dict):
                    for name, value in raw_cookies.items():
                        cookie = {
                            "name": name,
                            "value": value,
                            "url": "https://notebooklm.google.com", 
                            "secure": True  # Most Google cookies are secure
                        }
                        # Remove specific attributes if they conflict with 'url'
                        # Broadly applying for now.
                        cookies.append(cookie)
            return cookies
    except Exception as e:
        print(f"❌ Error parsing cookies: {e}")
        return None

async def create_and_upload(file_path, title_hint=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True) # Set False to watch it
        context = await browser.new_context()
        cookies = await load_cookies()
        if cookies: await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto("https://notebooklm.google.com/")
        
        # Smart Logic: Check if a notebook with the topic name already exists
        topic_found = False
        if title_hint:
            try:
                # Look for the topic name in the dashboard
                topic_link = page.get_by_text(title_hint, exact=False).first
                if await topic_link.is_visible():
                    print(f"🔗 Found existing notebook for: {title_hint}. Merging...")
                    await topic_link.click()
                    await page.wait_for_url("**/notebook/**")
                    topic_found = True
            except:
                pass

        if not topic_found:
            print(f"✨ Creating NEW notebook. (Hint was: {title_hint})")
            # Try English then Chinese
            try:
                await page.get_by_text("New Notebook", exact=False).first.click(timeout=3000)
            except:
                await page.get_by_text("建立新的筆記本", exact=False).first.click()
                
            await page.wait_for_url("**/notebook/**")
            # We DON'T rename it here. We let NotebookLM auto-name it based on the first upload.

        # Upload
        try:
            async with page.expect_file_chooser() as fc_info:
                inputs = await page.query_selector_all("input[type='file']")
                if inputs:
                    await inputs[0].set_input_files(file_path)
                else:
                    # Fallback click (English / Chinese)
                    try:
                        await page.click("text=Source", timeout=2000)
                    except:
                        await page.click("text=來源") # Or '新增來源'
                        
        except Exception as e:
            print(f"Upload warning: {e}")

        await asyncio.sleep(15) # Wait for upload (Increased to 15s)
        
        # Get final title (NotebookLM might have auto-named it)
        final_title = "Untitled"
        try:
            title_el = page.locator("input[aria-label='Notebook title']")
            # Try Chinese label if English fails
            if await title_el.count() == 0:
                 title_el = page.locator("input[aria-label='筆記本標題']")
            if await title_el.count() > 0:
                final_title = await title_el.input_value()
        except:
            pass

        await browser.close()
        return final_title

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(1)
        
    target_file = sys.argv[1]
    title_arg = sys.argv[2] if len(sys.argv) > 2 else None
    
    asyncio.run(create_and_upload(target_file, title_arg))
