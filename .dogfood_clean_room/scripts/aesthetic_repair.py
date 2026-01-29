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
        processed_count = 0
        all_folders = [f for f in os.listdir(ROOT_DIR) if os.path.isdir(os.path.join(ROOT_DIR, f)) and f not in [".gemini", "input_thoughts"]]
        
        print(f"📂 Scanning {len(all_folders)} folders for aesthetic improvements...")

        for item in all_folders:
            item_path = os.path.join(ROOT_DIR, item)
            
            # Try to find a match in notebook_map
            target_match = None
            
            # Clean folder name for better matching (remove prefixes and timestamps)
            clean_item = item.replace("DONE_", "").replace("MASTER SYNTHESIS", "").strip()
            # Remove timestamp patterns if any (e.g., 2026年...)
            for i in range(len(clean_item)):
                if clean_item[i:].startswith("202"):
                    clean_item = clean_item[:i].strip()
                    break

            # Strategy 1: Exact match or fuzzy inclusion
            for title, aes_name in notebook_map.items():
                if title.lower() in clean_item.lower() or clean_item.lower() in title.lower():
                    target_match = aes_name
                    break
                
                # Strategy 2: Keyword matching for known technical labels
                keywords = ["Pixel Echo", "像素共鳴", "Agent-Based", "自優化", "FlashSquirrel", "Automated Research", "光速研究", "Privacy", "數據隱私"]
                for kw in keywords:
                    if kw.lower() in clean_item.lower() and kw.lower() in title.lower():
                        target_match = aes_name
                        break
                if target_match: break
            
            # Strategy 3: Final Force Mapping for specific messy ones
            force_map = {
                "Agent-Based": "🔄 自優化研究流水線：認知卸載與語意反向傳播系統",
                "Automated Research": "⚡ 光速研究：全自動知識代謝系統報告",
                "Pixel Echo": "👾 像素共鳴：WLW 去社交感官實驗室研究報告",
                "FlashSquirrel": "🐿️ FlashSquirrel：AI 自動化研究管道與隱私架構分析",
                "行動研究": "🛡️ 行動研究應用程式之數據隱私分析",
                "隱私": "🛡️ 行動研究應用程式之數據隱私分析"
            }
            if not target_match:
                for k, v in force_map.items():
                    if k.lower() in item.lower() or item.lower() in k.lower():
                        target_match = v
                        break
            
            if target_match:
                new_path = os.path.join(ROOT_DIR, target_match)
                if new_path != item_path:
                    try:
                        if os.path.exists(new_path):
                            # If it exists, merge them or keep the newer one? 
                            # For safety, let's add a small suffix if it's a different folder
                            new_path = new_path + "_" + item[:5] 
                        
                        os.rename(item_path, new_path)
                        print(f"✅ Aesthetic Fixed: {item} -> {os.path.basename(new_path)}")
                        processed_count += 1
                    except Exception as e:
                        print(f"❌ Failed to rename {item}: {e}")
            else:
                # print(f"❓ Could not find a NotebookLM match for: {item}")
                pass

        print(f"✨ Aesthetic Migration Complete. {processed_count} folders updated.")

if __name__ == "__main__":
    asyncio.run(aesthetic_migration())
