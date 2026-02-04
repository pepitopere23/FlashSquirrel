import os
import json
import sys
import asyncio
from typing import List, Optional, Dict, Any
from playwright.async_api import async_playwright

# Import Alert System
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from alert_system import trigger_red_light
except ImportError:
    def trigger_red_light(msg): print(f"🚨 Mock Alert: {msg}")

# Persistent Profile Path
USER_DATA_DIR = os.path.expanduser("~/.notebooklm-mcp/chrome_profile")

def get_mapping(map_file: str, topic: str) -> Optional[str]:
    """Retrieves the mapped notebook title for a given topic."""
    if not os.path.exists(map_file):
        return None
    try:
        with open(map_file, 'r', encoding='utf-8') as f:
            mapping: Dict[str, str] = json.load(f)
            return mapping.get(topic)
    except Exception:
        return None

def save_mapping(map_file: str, topic: str, notebook_title: str) -> None:
    """Saves or updates the mapping between a topic and a notebook title."""
    mapping: Dict[str, str] = {}
    if os.path.exists(map_file):
        try:
            with open(map_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
        except Exception as e:
            print(f"⚠️ Mapping error ignored: {e}")

    mapping[topic] = notebook_title
    try:
        with open(map_file, 'w', encoding='utf-8') as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️ Failed to save mapping: {e}")
    return None

async def create_and_upload(file_path: str, title_hint: Optional[str] = None, map_file: Optional[str] = None, topic_id: Optional[str] = None) -> str:
    """
    Orchestrates the Playwright automation using PERSISTENT CONTEXT.
    """
    # Create profile dir if needed
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    
    async with async_playwright() as p:
        try:
            # V4: Persistent Context (Long-term Memory)
            # This uses the same user data spanning across sessions
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=True, # Set to False for debugging
                args=["--disable-blink-features=AutomationControlled"] # Basic stealth
            )
        except Exception as e:
            msg = f"Browser Launch Failed: {e}"
            print(f"❌ {msg}")
            trigger_red_light(msg)
            return "Failed"

        page = await browser.new_page() if not browser.pages else browser.pages[0]
        
        try:
            await page.goto("https://notebooklm.google.com/")
            
            # Auth Check: Look for "New Notebook" or Login Prompt
            try:
                # Wait for either 'New Notebook' (Success) or 'Sign in' (Fail)
                await page.wait_for_selector("button:has-text('New Notebook'), button:has-text('建立新的筆記本'), a[href*='accounts.google.com']", timeout=10000)
                
                # Check if we are redirected to login
                if "accounts.google.com" in page.url or await page.get_by_text("Sign in").count() > 0:
                    raise Exception("Auth Required (Cookie Expired)")
            except Exception as e:
                # If we timed out or found login page
                raise Exception(f"Authentication Check Failed: {e}")

            topic_found = False
            # Phase I: Stable ID Mapping
            mapping_key = topic_id if topic_id else title_hint
            mapped_title = get_mapping(map_file, mapping_key) if map_file and mapping_key else None
            
            search_targets = []
            if mapped_title: search_targets.append(mapped_title)
            if title_hint: search_targets.append(title_hint)
            # Clean topic (remove DONE_ prefix)
            clean_topic = title_hint.replace("DONE_", "") if title_hint else None
            if clean_topic: search_targets.append(clean_topic)

            for target in search_targets:
                if topic_found: break
                try:
                    # Use exact matching to prevent accidental merging of different topics
                    topic_link = page.get_by_text(target, exact=True).first
                    if await topic_link.is_visible(timeout=3000):
                        print(f"🔗 Found existing notebook with exact match for: {target}. Merging...")
                        await topic_link.click()
                        await page.wait_for_url("**/notebook/**", timeout=10000)
                        topic_found = True
                except:
                    continue

            if not topic_found:
                print(f"✨ Creating NEW notebook. (Target: {title_hint})")
                try:
                    await page.wait_for_selector(".cdk-overlay-backdrop", state="hidden", timeout=3000)
                except Exception as e:
                    print(f"⚠️ Overlay check failed: {e}")

                try:
                    await page.get_by_text("New Notebook", exact=False).first.click(timeout=3000, force=True)
                except Exception:
                    await page.get_by_text("建立新的筆記本", exact=False).first.click(force=True)
                await page.wait_for_url("**/notebook/**", timeout=60000)

            # Upload Logic
            try:
                await asyncio.sleep(5)
                async with page.expect_file_chooser(timeout=60000) as fc_info:
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
            
            # --- LAYER 1: Dashboard Property Scanning (Fast) ---
            async def get_dashboard_title():
                try:
                    await page.goto("https://notebooklm.google.com/")
                    await asyncio.sleep(5)
                    # We look for the most recent card that isn't untitled
                    cards = await page.locator("mat-card").all()
                    for card in cards:
                        aria = await card.get_attribute("aria-label")
                        if aria and "Untitled" not in aria and "未命名" not in aria:
                            # If we have a hint, verify it matches
                            if title_hint and title_hint.lower() in aria.lower():
                                return aria.strip()
                        
                        text = await card.inner_text()
                        lines = [l.strip() for l in text.split("\n") if l.strip()]
                        if len(lines) >= 3 and "Untitled" not in lines[2] and "未命名" not in lines[2]:
                            if not title_hint or (title_hint.lower() in lines[2].lower()):
                                emoji = lines[0] if len(lines[0]) < 3 else ""
                                return f"{emoji} {lines[2]}".strip()
                except:
                    pass
                return None

            # --- LAYER 2: Inner Page Input Extraction (Deep) ---
            async def get_inner_title():
                try:
                    if "notebook" not in page.url:
                        first_card = page.locator("mat-card").first
                        await first_card.click()
                        await page.wait_for_url("**/notebook/**", timeout=15000)
                    
                    title_el = page.locator("input[aria-label='Notebook title'], input[aria-label='筆記本標題']")
                    for _ in range(12): # Wait up to 60s
                        val = await title_el.input_value()
                        if val and "Untitled" not in val and "未命名" not in val:
                            return val.strip()
                        await asyncio.sleep(5)
                except:
                    pass
                return None

            # Execution Flow: 1 -> 2 -> Fallback
            result = await get_dashboard_title()
            if not result:
                print("🔄 Dashboard scan failed. Trying Inner Page...")
                result = await get_inner_title()
            
            if result:
                final_title = result
            else:
                # --- LAYER 3: Title Hint Fallback (The Iron Hand) ---
                print("⚠️ Auto-naming failed. Using Title Hint as fallback.")
                final_title = title_hint if title_hint else "Untitled Research"

            if map_file and mapping_key:
                save_mapping(map_file, mapping_key, final_title)

            await browser.close()
            print(f"RESULT:{final_title}") # Reliable output for shell capture
            return final_title

        except Exception as e:
            # GLOBAL ERROR TRAP -> RED LIGHT
            error_msg = str(e)
            print(f"🔥 CRITICAL FAIL: {error_msg}")
            trigger_red_light(f"Automation Error: {error_msg}")
            
            if 'browser' in locals():
                await browser.close()
            
            # Re-raise so the pipeline knows it failed
            raise e

if __name__ == "__main__":
    if len(sys.argv) < 2: sys.exit(1)
    target_file = sys.argv[1]
    title_arg = sys.argv[2] if len(sys.argv) > 2 else None
    mapping_file = sys.argv[3] if len(sys.argv) > 3 else None
    topic_id_arg = sys.argv[4] if len(sys.argv) > 4 else None
    asyncio.run(create_and_upload(target_file, title_arg, mapping_file, topic_id_arg))

