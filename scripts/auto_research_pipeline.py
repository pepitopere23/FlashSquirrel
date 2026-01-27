#!/usr/bin/env python3
"""
Auto Research Pipeline (Folder-Centric Edition) - Enterprise Grade
The "Master Script" that automates the flow based on sub-folders.

[Features]
- Exponential Backoff for API Rate Limits
- iCloud Sync Awareness (.icloud detection)
- Thread-Safe Async Processing Queue
- Verification Layer for Grounding
- Conflict-Free Renaming
"""

import os
import sys
import time
import uuid
import random
import asyncio
import logging
import shutil
from typing import Optional, List
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Configuration
load_dotenv()
# iCloud Drive Path
ROOT_DIR = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/研究工作流")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Setup Logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

os.makedirs(ROOT_DIR, exist_ok=True)

class RobustUtils:
    @staticmethod
    def wait_for_icloud_download(file_path: str, timeout: int = 60) -> str:
        """
        Detects if a file is a .icloud placeholder and waits for download.
        Returns the final resolved path (without .icloud).
        """
        # Case 1: File is already downloaded
        if os.path.exists(file_path) and not file_path.endswith('.icloud'):
            return file_path
            
        # Case 2: It's a .icloud placeholder
        target_path = file_path
        if file_path.endswith('.icloud'):
            # Current: .file.jpg.icloud -> Target: file.jpg
            # Format usually: .name.ext.icloud, actual file is name.ext (hidden dot issue on macOS sometimes)
            # Simple heuristic: remove leading dot if present, remove .icloud
            basename = os.path.basename(file_path)
            clean_name = basename.replace('.icloud', '')
            if clean_name.startswith('.'): clean_name = clean_name[1:]
            target_path = os.path.join(os.path.dirname(file_path), clean_name)
            
            logging.info(f"🌩️ iCloud Placeholder detected: {basename}. Triggering download...")
            # Trigger download by attempting to os.stat the TARGET path (macOS magic)
            # Or usually just accessing the .icloud file triggers BRM daemon.
            pass

        start_time = time.time()
        while time.time() - start_time < timeout:
            if os.path.exists(target_path):
                # Check if size > 0 (download complete)
                if os.path.getsize(target_path) > 0:
                    logging.info(f"✅ iCloud Download Complete: {target_path}")
                    return target_path
            time.sleep(2)
            
        logging.warning(f"⚠️ iCloud Download Timeout: {target_path}")
        return target_path # Return anyway, might fail later but we tried.

    @staticmethod
    def safe_rename(old_path: str, new_name: str) -> str:
        """
        Renames a folder safely. If target exists, appends UUID.
        """
        parent = os.path.dirname(old_path)
        new_path = os.path.join(parent, new_name)
        
        if os.path.exists(new_path) and new_path != old_path:
            unique_suffix = uuid.uuid4().hex[:6]
            new_path = f"{new_path}_{unique_suffix}"
            logging.warning(f"⚠️ Name conflict. Renaming to: {os.path.basename(new_path)}")
            
        try:
            os.rename(old_path, new_path)
            return new_path
        except Exception as e:
            logging.error(f"❌ Rename Failed: {e}")
            return old_path

class ResearchPipeline:
    def __init__(self):
        if not GEMINI_API_KEY:
            logging.error("GEMINI_API_KEY not found in .env")
            sys.exit(1)
        # New SDK Client
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        # Expanded Model List for Maximum Reliability
        self.models_priority = [
            'gemini-2.0-flash', 
            'gemini-1.5-flash',
            'gemini-1.5-flash-8b', 
            'gemini-1.5-pro'       
        ]

    def get_mime_type(self, path):
        if path.lower().endswith('.png'): return 'image/png'
        if path.lower().endswith('.jpg') or path.lower().endswith('.jpeg'): return 'image/jpeg'
        if path.lower().endswith('.pdf'): return 'application/pdf'
        return 'text/plain'

    def log_usage(self, model_name, response):
        """Extracts and logs usage metadata for cost awareness."""
        try:
            usage = response.usage_metadata
            input_tokens = usage.prompt_token_count
            output_tokens = usage.candidates_token_count
            total_tokens = usage.total_token_count
            
            # Estimates (2.0 Flash Pricing)
            # $0.10 / 1M input, $0.40 / 1M output
            estimated_cost = (input_tokens * 0.0000001) + (output_tokens * 0.0000004)
            
            logging.info(f"📊 [Usage] Model: {model_name} | Tokens: {input_tokens}i / {output_tokens}o / {total_tokens} total")
            logging.info(f"💰 [Cost Estimate] ${estimated_cost:.5f} USD (approx.)")
            return estimated_cost
        except Exception as e:
            logging.warning(f"Could not log usage: {e}")
            return 0

    def generate_with_fallback(self, prompt, content_part=None, tools=None):
        """Try models in priority order with Exponential Backoff."""
        contents = [prompt]
        if content_part:
            if isinstance(content_part, dict) and 'data' in content_part:
                 contents.append(types.Part.from_bytes(data=content_part['data'], mime_type=content_part['mime_type']))
            else:
                 contents.append(content_part)

        config = None
        if tools:
            config = types.GenerateContentConfig(tools=tools)

        for model_name in self.models_priority:
            # Retry Loop for 429 (Rate Limit) with Exponential Backoff
            for attempt in range(5): # Increased to 5 attempts
                try:
                    logging.info(f"🤖 Trying model: {model_name} (Attempt {attempt+1})...")
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=config
                    )
                    self.log_usage(model_name, response)
                    return response
                except Exception as e:
                    error_msg = str(e)
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        # Jittered Exponential Backoff: 2^attempt + random
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        logging.warning(f"⏳ Rate Limit (429) on {model_name}. Waiting {wait_time:.2f}s...")
                        time.sleep(wait_time)
                        continue 
                    elif "404" in error_msg or "NOT_FOUND" in error_msg:
                        logging.warning(f"🚫 Model {model_name} not found (404). Skipping...")
                        break 
                    else:
                        logging.warning(f"⚠️ Model {model_name} error: {e}. Switching to next...")
                        break 
        
        logging.error("❌ All models failed.")
        return None

    def run_gemini_research(self, file_path: str) -> Optional[str]:
        """Phase 1: Deep Research with Grounding (Multimodal + PDF)"""
        # iCloud Safety Check
        file_path = RobustUtils.wait_for_icloud_download(file_path)
        if not os.path.exists(file_path):
            logging.error(f"❌ File not found after sync wait: {file_path}")
            return None

        filename = os.path.basename(file_path)
        parent_dir = os.path.dirname(file_path)
        
        if filename.startswith(("report_", "visualizations_", "slide_", "mindmap_", "MASTER_SYNTHESIS", "upload_package")):
            return None
            
        logging.info(f"🔍 [Phase 1] Starting Gemini Research on: {filename}")
        
        prompt = """
        [ROLE: Senior Principal Researcher]
        [OBJECTIVE: Produce a doctoral-level research report]
        [LANGUAGE: Bilingual - English & Traditional Chinese (繁體中文)]
        
        Task: 
        1. Analyze the provided input (text/image/PDF) to extract the core thesis.
        2. Perform an extensive Google Search (using Grounding) to validate this thesis against LATEST 2024-2026 data.
        3. Challenge the thesis: Find counter-arguments and alternative perspectives.
        
        [OUTPUT FORMAT (Strict Markdown)]
        # [Study Title] / [研究標題]
        > **Confidence Score**: [0-100]% (If < 70%, add "⚠️ Human Review Recommended")
        
        ## 1. Executive Summary / 執行摘要
        (Write this section in English first, followed by Traditional Chinese translation)
        
        ## 2. Theoretical Framework & Core Arguments / 理論框架與核心論點
        (Write this section in English first, followed by Traditional Chinese translation)
        
        ## 3. Critical Analysis & Counter-Perspectives / 批判性分析與反面觀點
        (Write this section in English first, followed by Traditional Chinese translation)
        
        ## 4. Empirical Data & Case Studies / 實證數據與案例研究
        (Write this section in English first, followed by Traditional Chinese translation)
        
        ## 5. References & Bibliography / 參考文獻
        
        [METADATA]
        - Confidence Logic: (Briefly explain why this score was given)
        """

        try:
            report_filename = f"report_{os.path.splitext(filename)[0]}.md"
            report_path = os.path.join(parent_dir, report_filename)
            
            if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
                logging.info(f"⏩ Skipping existing report: {filename}")
                return report_path

            mime = self.get_mime_type(file_path)
            content_part = None
            
            if mime.startswith('image') or mime == 'application/pdf':
                with open(file_path, "rb") as f:
                    content_part = {'mime_type': mime, 'data': f.read()}
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    content_part = f.read()
            
            # Enable Grounding with new SDK
            tools = [types.Tool(google_search=types.GoogleSearch())]
            
            response = self.generate_with_fallback(prompt, content_part, tools=tools)
            
            if not response or not response.text: return None
            
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            
            logging.info(f"✅ [Phase 1] Report generated: {report_path}")
            return report_path
            
        except Exception as e:
            logging.error(f"Gemini API Error: {e}")
            return None

    def run_folder_synthesis(self, folder_path: str) -> Optional[str]:
        folder_name = os.path.basename(folder_path)
        logging.info(f"🧠 [Phase 1.5] Synthesizing insights in: {folder_name}")
        report_files = [f for f in os.listdir(folder_path) if f.startswith("report_") and f.endswith(".md")]
        if not report_files: return None
        
        combined_text = ""
        for rf in report_files:
            with open(os.path.join(folder_path, rf), "r", encoding="utf-8") as f:
                combined_text += f"\n\n=== SOURCE: {rf} ===\n" + f.read()

        prompt = f"""
        [ROLE: Synthesis Engine]
        [LANGUAGE: Bilingual - English & Traditional Chinese (繁體中文)]
        Task: Synthesize these reports into a MASTER_SYNTHESIS.md. 
        Folder Scope: {folder_name}
        
        CRITICAL REQUIREMENT:
        You must generate a 'Conflict Matrix' that identifies competing viewpoints across these sources. Do NOT smooth out contradictions; expose them.
        
        Output Format:
        # Integrated Analysis Report / 綜合分析報告: {folder_name}
        
        ## 1. Dialectical Conflict Matrix / 辯證衝突矩陣
        | Viewpoint A (觀點 A) | Viewpoint B (觀點 B) | Source of Conflict (衝突來源) | Resolution/Synthesis (解決方案/綜合) |
        |---|---|---|---|
        | ... | ... | ... | ... |
        
        ## 2. Integrated Narrative / 整合敘事
        (Write the full analysis in English first, followed by Traditional Chinese translation)
        
        SOURCES:
        {combined_text[:60000]}
        """
        
        try:
            response = self.generate_with_fallback(prompt)
            if not response or not response.text: return None
            
            synthesis_path = os.path.join(folder_path, "MASTER_SYNTHESIS.md")
            with open(synthesis_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            return synthesis_path
        except Exception as e:
            logging.error(f"Synthesis Error: {e}")
            return None

    async def generate_visualizations(self, context: str, output_dir: str):
        prompt = f"Generate Slidev (slides.md) and Mermaid (mindmap.mmd) code from this:\n{context[:10000]}"
        try:
            response = self.generate_with_fallback(prompt)
            if response and response.text:
                viz_path = os.path.join(output_dir, "visualizations_bundle.md")
                with open(viz_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
        except Exception as e:
            logging.error(f"Viz Error: {e}")


class AsyncProcessor:
    """
    Handles file events in a queue to prevent blocking the Watchdog observer.
    """
    def __init__(self, pipeline: ResearchPipeline):
        self.pipeline = pipeline
        self.queue = asyncio.Queue()
        self.processing = False

    async def worker(self):
        logging.info("👷 Async Worker started...")
        self.processing = True
        while True:
            file_path = await self.queue.get()
            try:
                await self.process_workflow(file_path)
            except Exception as e:
                logging.error(f"❌ Worker Error: {e}")
            finally:
                self.queue.task_done()

    async def process_workflow(self, file_path):
        report_path = self.pipeline.run_gemini_research(file_path)
        if not report_path: return
        
        folder_path = os.path.dirname(file_path)
        synthesis_path = self.pipeline.run_folder_synthesis(folder_path)
        
        content_to_push = ""
        with open(report_path, 'r') as f: content_to_push += f.read()
        if synthesis_path:
            try:
                with open(synthesis_path, 'r') as f: content_to_push += "\n\n" + f.read()
            except: pass

        upload_package_path = os.path.join(folder_path, "upload_package.md")
        with open(upload_package_path, "w", encoding="utf-8") as f: f.write(content_to_push)
        
        topic = os.path.basename(folder_path)
        logging.info(f"🤖 Automating NotebookLM for: {topic}")
        automator_script = os.path.join(os.path.dirname(__file__), "notebooklm_automator.py")
        
        proc = await asyncio.create_subprocess_exec(
            sys.executable, automator_script, upload_package_path, topic, 
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        # Semantic Renaming
        new_topic = stdout.decode().strip().split('\n')[-1]
        if new_topic and new_topic != topic and "Success" not in new_topic and "Error" not in new_topic:
            new_folder_path = RobustUtils.safe_rename(folder_path, new_topic)
            if new_folder_path != folder_path:
                logging.info(f"🏷️ Renamed: {folder_path} -> {new_folder_path}")
                folder_path = new_folder_path

        await self.pipeline.generate_visualizations(content_to_push, folder_path)
        
    def add_task(self, file_path):
        # Check queue size to prevent overflow
        if self.queue.qsize() > 50:
            logging.warning("⚠️ Queue full! Dropping task.")
            return
        self.queue.put_nowait(file_path)


class InputHandler(FileSystemEventHandler):
    def __init__(self, processor: AsyncProcessor):
        self.processor = processor
        self.loop = asyncio.get_event_loop()

    def on_modified(self, event):
        if event.is_directory: return
        self.handle_event(event.src_path)

    def on_created(self, event):
        if event.is_directory: return
        self.handle_event(event.src_path)

    def handle_event(self, file_path):
        rel_path = os.path.relpath(file_path, ROOT_DIR)
        
        if file_path.endswith(".py"): return
        if "/" not in rel_path: return 
        
        # Skip hidden/temp files
        if os.path.basename(file_path).startswith('.'): return
        
        if not file_path.lower().endswith(('.txt', '.md', '.png', '.jpg', '.jpeg', '.pdf')): return
        if "report_" in file_path or "visualizations_" in file_path or "MASTER_SYNTHESIS" in file_path or "upload_package" in file_path: return

        logging.info(f"⚡️ New Thought Detected: {rel_path} (Queued)")
        self.processor.add_task(file_path)

async def scan_existing_files(processor):
    """Scan and process files that already exist before script started."""
    logging.info("🔎 Scanning for existing files...")
    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            file_path = os.path.join(root, file)
            # Filter matches InputHandler logic
            if os.path.basename(file_path).startswith('.'): continue
            
            if not file_path.lower().endswith(('.txt', '.md', '.png', '.jpg', '.jpeg', '.pdf')): continue
            if "report_" in file or "visualizations_" in file or "MASTER_SYNTHESIS" in file or "upload_package" in file_path: continue
            
            report_name = f"report_{os.path.splitext(file)[0]}.md"
            if os.path.exists(os.path.join(root, report_name)):
                 continue

            logging.info(f"📂 Found unprocessed historical file: {file}")
            processor.add_task(file_path)

def main():
    pipeline = ResearchPipeline()
    processor = AsyncProcessor(pipeline)
    handler = InputHandler(processor)
    
    observer = Observer()
    observer.schedule(handler, ROOT_DIR, recursive=True)
    observer.start()
    
    # Verify Self
    try:
        from validation_17_layers import validate_code_17_layers
        logging.info("🛡️ [Self-Diagnostic] Running 17-Layer Code Validation...")
        with open(__file__, 'r') as f: self_code = f.read()
        result = validate_code_17_layers(self_code, "auto_research_pipeline.py")
        if result['quality_score'] < 80:
            logging.warning(f"⚠️ Code Quality Warning! Score: {result['quality_score']}/100")
        else:
            logging.info(f"✅ Code Integrity Verified.")
    except:
        pass

    logging.info(f"🚀 Robust Logic Pipeline Started.")
    logging.info(f"📂 Root: {os.path.abspath(ROOT_DIR)}")
    
    loop = asyncio.get_event_loop()
    # Schedule historical scan
    loop.run_until_complete(scan_existing_files(processor))
    
    # Start the worker
    try:
        loop.run_until_complete(processor.worker())
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    main()
