#!/usr/bin/env python3
import os
import json
import asyncio
from playwright.async_api import async_playwright

ROOT_DIR = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/研究工作流")
AUTH_FILE = os.path.expanduser("~/.notebooklm-mcp/auth.json")

async def aesthetic_migration():
    print("🎨 Starting Aesthetic Migration (Emoji-to-Emoji Sync)...")
    
    if not os.path.exists(AUTH_FILE):
        print("❌ Auth file not found.")
        return

    with open(AUTH_FILE, "r") as f:
        data = json.load(f)
        cookies = []
        raw_cookies = data.get("cookies", {})
        if isinstance(raw_cookies, dict):
            for n, v in raw_cookies.items():
                cookies.append({"name": n, "value": v, "url": "https://notebooklm.google.com", "secure": True})

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        await context.add_cookies(cookies)
        page = await context.new_page()
        await page.goto("https://notebooklm.google.com/")
        await asyncio.sleep(8)
        
        cards = await page.query_selector_all("mat-card")
        notebook_map = {}
        for card in cards:
            text = await card.inner_text()
            lines = [l.strip() for l in text.split("\n") if l.strip()]
            if len(lines) >= 3:
                emoji = lines[0]
                title = lines[2]
                if title and "來源" not in title and title != "more_vert":
                    full_name = f"{emoji} {title}"
                    notebook_map[title] = full_name
        
        await browser.close()
        
        print(f"📊 Captured {len(notebook_map)} professional titles from NotebookLM.")
        
        # Now rename folders
        for item in os.listdir(ROOT_DIR):
            item_path = os.path.join(ROOT_DIR, item)
            if not os.path.isdir(item_path) or item in [".gemini", "input_thoughts"]:
                continue
                
            # Try to find a match in notebook_map
            # Folders might have prefixes like DONE_, PENDING_, or debug strings
            target_match = None
            
            # Strategy: Search if any of our notebook titles are contained in the messy folder name
            # Or if keywords from the notebook title match the folder content
            for title, aes_name in notebook_map.items():
                # Exact inclusion
                if title in item or item in title:
                    target_match = aes_name
                    break
                
                # Keyword matching for known technical labels
                keywords = ["Pixel Echo", "像素共鳴", "Agent-Based", "自優化", "FlashSquirrel", "Automated Research", "光速研究", "Privacy", "數據隱私"]
                for kw in keywords:
                    if kw.lower() in item.lower() and kw.lower() in title.lower():
                        target_match = aes_name
                        break
                if target_match: break
            
            # Final Force Mapping for the last 3 messy ones
            force_map = {
                "Agent-Based Self-Optimizing": "🔄 自優化研究流水線：認知卸載與語意反向傳播系統",
                "Automated Research Pipelines": "⚡ 光速研究：全自動知識代謝系統報告",
                "Pixel Echo": "👾 像素共鳴：去社交化感官實驗研究報告"
            }
            if not target_match:
                for k, v in force_map.items():
                    if k in item:
                        target_match = v
                        break
            
            if target_match:
                new_path = os.path.join(ROOT_DIR, target_match)
                if new_path != item_path:
                    try:
                        if os.path.exists(new_path):
                            print(f"⚠️ Conflict: {target_match} already exists. Skipping.")
                        else:
                            os.rename(item_path, new_path)
                            print(f"✅ Aesthetic Fixed: {item} -> {target_match}")
                    except Exception as e:
                        print(f"❌ Failed to rename {item}: {e}")
            else:
                print(f"❓ Could not find a NotebookLM match for: {item}")

if __name__ == "__main__":
    asyncio.run(aesthetic_migration())
