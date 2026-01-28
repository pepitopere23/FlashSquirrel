import os
import json
import sys
import asyncio
import difflib
from playwright.async_api import async_playwright

AUTH_FILE = os.path.expanduser("~/.notebooklm-mcp/auth.json")

async def load_cookies():
    if not os.path.exists(AUTH_FILE):
        return None
    try:
        with open(AUTH_FILE, 'r') as f:
            data = json.load(f)
            cookies = []
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
                elif isinstance(raw_cookies, dict):
                    for name, value in raw_cookies.items():
                        cookies.append({
                            "name": name,
                            "value": value,
                            "url": "https://notebooklm.google.com", 
                            "secure": True
                        })
            return cookies
    except:
        return None

def get_mapping(map_file, topic):
    if not os.path.exists(map_file):
        return None
    try:
        with open(map_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
            return mapping.get(topic)
    except:
        return None

def save_mapping(map_file, topic, notebook_title):
    mapping = {}
    if os.path.exists(map_file):
        try:
            with open(map_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
        except:
            pass
    mapping[topic] = notebook_title
    try:
        with open(map_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to save mapping: {e}")

async def create_and_upload(file_path, title_hint=None, map_file=None):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        cookies = await load_cookies()
        if cookies: await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto("https://notebooklm.google.com/")
        
        topic_found = False
        mapped_title = get_mapping(map_file, title_hint) if map_file and title_hint else None
        
        search_targets = []
        if mapped_title: search_targets.append(mapped_title)
        if title_hint: search_targets.append(title_hint)
        # Clean topic (remove DONE_ prefix)
        clean_topic = title_hint.replace("DONE_", "") if title_hint else None
        if clean_topic: search_targets.append(clean_topic)

        for target in search_targets:
            if topic_found: break
            try:
                # Use a specific selector for the notebook cards in the dashboard
                # NotebookLM dashboard usually has cards with text
                topic_link = page.get_by_text(target, exact=False).first
                if await topic_link.is_visible(timeout=3000):
                    print(f"🔗 Found existing notebook for: {target}. Merging...")
                    await topic_link.click()
                    await page.wait_for_url("**/notebook/**", timeout=10000)
                    topic_found = True
            except:
                continue

        if not topic_found:
            print(f"✨ Creating NEW notebook. (Target: {title_hint})")
            try:
                await page.wait_for_selector(".cdk-overlay-backdrop", state="hidden", timeout=3000)
            except: pass

            try:
                await page.get_by_text("New Notebook", exact=False).first.click(timeout=3000, force=True)
            except:
                await page.get_by_text("建立新的筆記本", exact=False).first.click(force=True)
            await page.wait_for_url("**/notebook/**", timeout=15000)

        # Upload Logic
        try:
            await asyncio.sleep(5)
            async with page.expect_file_chooser(timeout=15000) as fc_info:
                upload_btn = page.get_by_text("上傳檔案", exact=False)
                if await upload_btn.count() > 0:
                    await upload_btn.first.click(force=True)
                else:
                    await page.get_by_text("Upload files", exact=False).first.click(force=True)
            
            file_chooser = await fc_info.value
            await file_chooser.set_files(file_path)
            print(f"🚀 File selected and uploading: {os.path.basename(file_path)}")
        except Exception as e:
            print(f"⚠️ Upload trigger failed: {e}")
            # Try setting input directly
            inputs = await page.query_selector_all("input[type='file']")
            if inputs: await inputs[0].set_input_files(file_path)

        # Wait for processing and auto-naming
        await asyncio.sleep(25)
        
        final_title = "Untitled"
        try:
            # Try to catch the title from the input field
            title_el = page.locator("input[aria-label='Notebook title']")
            if await title_el.count() == 0:
                 title_el = page.locator("input[aria-label='筆記本標題']")
            
            if await title_el.count() > 0:
                final_title = await title_el.input_value()
                # If still "Untitled", wait a bit more
                if "Untitled" in final_title or "未命名" in final_title:
                    await asyncio.sleep(10)
                    final_title = await title_el.input_value()
            
            # Aesthetic Enhancement: Try to find the leading emoji
            # Usually in the notebook list or as a companion icon
            # For now, if we are in the notebook, the title in the input might not have the emoji
            # But we can capture it from the breadcrumbs or sidebar if available.
            # Simplified: Use a default emoji based on name if not found, 
            # or better: return to dashboard and find the card we just created.
            
            await page.goto("https://notebooklm.google.com/")
            await asyncio.sleep(5)
            # Find the card that matches our final_title
            cards = await page.query_selector_all("mat-card")
            for card in cards:
                text = await card.inner_text()
                lines = [l.strip() for l in text.split("\n") if l.strip()]
                if len(lines) >= 3 and final_title in lines[2]:
                    emoji = lines[0]
                    final_title = f"{emoji} {lines[2]}"
                    break
        except: pass

        if map_file and title_hint and final_title != "Untitled":
            save_mapping(map_file, title_hint, final_title)

        await browser.close()
        print(f"RESULT:{final_title}") # Reliable output for shell capture
        return final_title

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    target_file = sys.argv[1]
    title_arg = sys.argv[2] if len(sys.argv) > 2 else None
    mapping_file = sys.argv[3] if len(sys.argv) > 3 else None
    asyncio.run(create_and_upload(target_file, title_arg, mapping_file))
