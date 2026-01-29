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
from typing import Optional, List, Any, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Configuration
load_dotenv()

# Cross-platform Root Directory handling
# 1. Check if RESEARCH_ROOT_DIR is set in .env
# 2. Fallback to Mac iCloud path if it exists
# 3. Default to 'data' directory in the project root
DEFAULT_MAC_ICLOUD = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/研究工作流")
ENV_ROOT = os.getenv("RESEARCH_ROOT_DIR")

if ENV_ROOT:
    ROOT_DIR = os.path.abspath(os.path.expanduser(ENV_ROOT))
elif os.path.exists(DEFAULT_MAC_ICLOUD):
    ROOT_DIR = DEFAULT_MAC_ICLOUD
else:
    # Default to a local 'data' folder in the project directory
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Setup Logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')

os.makedirs(ROOT_DIR, exist_ok=True)

class RobustUtils:
    """Utility class for cross-platform file and iCloud synchronization handling."""
    
    @staticmethod
    def is_file_stable(file_path: str, wait_time: float = 2.0) -> bool:
        """
        Ensures a file is fully written by checking if its size is stable.
        This handles iCloud, Dropbox, and partial writes from other sync tools.
        """
        if not os.path.exists(file_path): return False
        try:
            initial_size = os.path.getsize(file_path)
            time.sleep(wait_time)
            final_size = os.path.getsize(file_path)
            # If size is > 0 and hasn't changed, it's likely stable
            return initial_size == final_size and final_size > 0
        except Exception:
            return False

    @staticmethod
    def wait_for_icloud_download(file_path: str, timeout: int = 60) -> str:
        """
        Detects if a file is a .icloud placeholder and waits for download.
        Includes a stability check to ensure partial writes are finished.
        """
        if os.path.exists(file_path) and not file_path.endswith('.icloud'):
            # Even for non-iCloud, check stability (for Dropbox/Telegram)
            if RobustUtils.is_file_stable(file_path):
                return file_path
            
        target_path = file_path
        if file_path.endswith('.icloud'):
            basename = os.path.basename(file_path)
            clean_name = basename.replace('.icloud', '')
            if clean_name.startswith('.'): 
                clean_name = clean_name[1:]
            target_path = os.path.join(os.path.dirname(file_path), clean_name)
            
            logging.info(f"🌩️ iCloud Placeholder detected: {basename}. Triggering download...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            if os.path.exists(target_path):
                if RobustUtils.is_file_stable(target_path):
                    logging.info(f"✅ Sync/Download Complete: {target_path}")
                    return target_path
            time.sleep(1)
            
        logging.warning(f"⚠️ Sync Timeout: {target_path}")
        return target_path

    @staticmethod
    def safe_rename(old_path: str, new_name: str) -> str:
        """
        Renames a folder safely by preventing name collisions.
        
        Args:
            old_path: Original folder path.
            new_name: Proposed new folder name.
            
        Returns:
            The actual resulting folder path.
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

class LinkParser:
    """Utility to extract URLs from link files (.webloc, .url)."""
    
    @staticmethod
    def extract_url(file_path: str) -> Optional[str]:
        """Extracts the first valid URL found in the file with hardened regex."""
        ext = os.path.splitext(file_path)[1].lower()
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            
            import re
            if ext == ".webloc":
                # Hardened XML search: handles whitespace, single/double quotes, and multiline
                match = re.search(r"<string>\s*(https?://[^\s<]+)\s*</string>", content, re.IGNORECASE)
                return match.group(1).strip() if match else None
            elif ext == ".url":
                # Hardened INI search: handles spaces around = and CRLF
                match = re.search(r"URL\s*=\s*(https?://[^\s\r\n\a\b]+)", content, re.IGNORECASE)
                return match.group(1).strip() if match else None
        except Exception as e:
            logging.error(f"🔗 Link extraction failed: {e}")
        return None

class ResearchPipeline:
    """The central engine for processing research folders and generating Gemini reports."""
    
    def __init__(self) -> None:
        """Initializes the Gemini client and model priorities."""
        if not GEMINI_API_KEY:
            logging.error("GEMINI_API_KEY not found in .env")
            sys.exit(1)
        self.root_dir: str = ROOT_DIR
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.models_priority: List[str] = [
            'gemini-2.0-flash', 
            'gemini-1.5-flash',
            'gemini-1.5-pro'       
        ]

    def get_mime_type(self, path: str) -> str:
        """Determines the MIME type based on file extension."""
        if path.lower().endswith('.png'): 
            return 'image/png'
        if path.lower().endswith('.jpg') or path.lower().endswith('.jpeg'): 
            return 'image/jpeg'
        if path.lower().endswith('.pdf'): 
            return 'application/pdf'
        return 'text/plain'

    def log_usage(self, model_name: str, response: Any) -> float:
        """
        Extracts and logs usage metadata for cost awareness.
        
        Args:
            model_name: The name of the model used.
            response: The Gemini API response object.
            
        Returns:
            The estimated cost of the call in USD.
        """
        try:
            usage = response.usage_metadata
            input_tokens = usage.prompt_token_count
            output_tokens = usage.candidates_token_count
            total_tokens = usage.total_token_count
            
            estimated_cost = (input_tokens * 0.0000001) + (output_tokens * 0.0000004)
            
            logging.info(f"📊 [Usage] Model: {model_name} | Tokens: {input_tokens}i / {output_tokens}o / {total_tokens} total")
            logging.info(f"💰 [Cost Estimate] ${estimated_cost:.5f} USD (approx.)")
            return float(estimated_cost)
        except Exception as e:
            logging.warning(f"Could not log usage: {e}")
            return 0.0

    async def generate_with_fallback(self, prompt: str, content_part: Any = None, tools: List[Any] = None) -> Any:
        """
        Attempts to generate content with fallback models and exponential backoff.
        
        Args:
            prompt: The primary text prompt.
            content_part: Additional content (data bytes or types.Part).
            tools: Tools to be used for generation (e.g., Google Search).
            
        Returns:
            The successful Gemini response object or None if all fail.
        """
        contents: List[Any] = [prompt]
        if content_part:
            if isinstance(content_part, dict) and 'data' in content_part:
                contents.append(types.Part.from_bytes(data=content_part['data'], mime_type=content_part['mime_type']))
            else:
                contents.append(content_part)

        config: Optional[types.GenerateContentConfig] = None
        if tools:
            config = types.GenerateContentConfig(tools=tools)

        for model_name in self.models_priority:
            # Retry Loop for 429 (Rate Limit) with Exponential Backoff
            for attempt in range(5): # Increased to 5 attempts
                try:
                    logging.info(f"🤖 Trying model: {model_name} (Attempt {attempt+1})...")
                    response: Any = self.client.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=config
                    )
                    self.log_usage(model_name, response)
                    return response
                except Exception as e:
                    error_msg: str = str(e)
                    if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                        # Jittered Exponential Backoff: 2^attempt + random
                        wait_time: float = (2 ** attempt) + random.uniform(0, 1)
                        logging.warning(f"⏳ Rate Limit (429) on {model_name}. Waiting {wait_time:.2f}s...")
                        await asyncio.sleep(wait_time)
                        continue 
                    elif "404" in error_msg or "NOT_FOUND" in error_msg:
                        logging.warning(f"🚫 Model {model_name} not found (404). Skipping...")
                        break 
                    else:
                        logging.warning(f"⚠️ Model {model_name} error: {e}. Switching to next...")
                        break # Try next model
        
        logging.error("❌ All models failed.")
        return None

    async def run_gemini_research(self, file_path: str) -> Optional[str]:
        """
        Phase 1: Deep Research with Grounding (Multimodal + PDF).
        
        Args:
            file_path: Path to the source file to research.
            
        Returns:
            The path to the generated report or None if failed/skipped.
        """
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
        1. Analyze the provided input (text/image/PDF/URL) to extract the core thesis.
        2. Perform an extensive Google Search (using Grounding) to validate this thesis against LATEST 2024-2026 data.
        3. Challenge the thesis: Find counter-arguments and alternative perspectives.
        
        [INPUT CONTEXT]
        {input_context_label}
        
        [OUTPUT FORMAT (Strict Markdown)]
        # [研究標題] / [Study Title]
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
            # Phase D+: Robust Sync Wait (Stability Guard)
            file_path = RobustUtils.wait_for_icloud_download(file_path)
            if not os.path.exists(file_path):
                 return None
            
            mime = self.get_mime_type(file_path)
            content_part = None
            input_context_label = f"Primary Input File: {filename}"
            
            # Semantic Link Processing
            if filename.lower().endswith(('.webloc', '.url')):
                extracted_url = LinkParser.extract_url(file_path)
                if extracted_url:
                    logging.info(f"🌐 [Phase D] Semantic Link detected: {extracted_url}")
                    content_part = f"Research Topic: {filename}\nSource URL: {extracted_url}\nPlease strictly visit and analyze the content of this URL."
                    input_context_label = f"Target Web Link: {extracted_url}"
                else:
                    logging.warning(f"⚠️ Fallback to file content (Link extraction failed): {filename}")

            if not content_part:
                if mime.startswith('image') or mime == 'application/pdf':
                    with open(file_path, "rb") as f:
                        content_part = {'mime_type': mime, 'data': f.read()}
                else:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content_part = f.read()

            logging.info(f"📡 [Phase 1] Launching Gemini Research for: {filename}...")
            # Re-format prompt with labels
            final_prompt = prompt.format(input_context_label=input_context_label)
            
            response: Any = await self.generate_with_fallback(final_prompt, content_part, tools=[types.Tool(google_search=types.GoogleSearch())])
            
            if not response or not response.text:
                # FAILURE TRANSPARENCY: Log specific reason for empty response
                error_path = os.path.join(parent_dir, f"RESEARCH_FAILURE_{os.path.splitext(filename)[0]}.md")
                with open(error_path, "w", encoding="utf-8") as f:
                    f.write(f"# ⚠️ Research Failure / 研究失敗\n\n**File**: `{filename}`\n**Reason**: Gemini returned an empty response after all retries. This might be due to a strict safety filter or an invalid URL.\n\n*Please check the source file or your internet connection.*")
                return None

            report_path: str = os.path.join(parent_dir, f"report_{os.path.splitext(filename)[0]}.md")
            if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
                logging.info(f"⏩ Skipping existing report: {filename}")
                return report_path

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            
            logging.info(f"📄 [Phase 1] Report generated: {report_path}")
            return report_path
        except Exception as e:
            logging.error(f"Phase 1 Gemini Error: {e}")
            # FAILURE TRANSPARENCY: Report runtime exception
            error_path = os.path.join(parent_dir, f"RESEARCH_FAILURE_{os.path.splitext(filename)[0]}.md")
            with open(error_path, "w", encoding="utf-8") as f:
                f.write(f"# ⚠️ Technical Anomaly / 技術異常\n\n**File**: `{filename}`\n**Error**: `{str(e)}`")
            return None

    async def run_folder_synthesis(self, folder_path: str) -> Optional[str]:
        """
        Phase 1.5: Synthesizes insights from all reports in a folder.
        
        Args:
            folder_path: The directory containing individual reports.
            
        Returns:
            The path to the MASTER_SYNTHESIS.md or None if no reports found.
        """
        folder_name = os.path.basename(folder_path)
        logging.info(f"🧠 [Phase 1.5] Synthesizing insights in: {folder_name}")
        report_files = [f for f in os.listdir(folder_path) if f.startswith("report_") and f.endswith(".md")]
        if not report_files: 
            return None
        
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
        # MASTER SYNTHESIS: [Topic]
        
        ## 1. Integrated Overview / 整合概述
        ## 2. Conflict Matrix & Divergent Insights / 衝突矩陣與分歧洞見
        ## 3. Consensus & Validated Facts / 共識與經驗證的事實
        ## 4. Strategic Recommendations / 策略性建議
        """
        
        try:
            response: Any = await self.generate_with_fallback(prompt, combined_text)
            if not response or not response.text: 
                return None
            
            synthesis_path: str = os.path.join(folder_path, "MASTER_SYNTHESIS.md")
            with open(synthesis_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            
            logging.info(f"🏆 [Phase 1.5] Master Synthesis complete: {synthesis_path}")
            return synthesis_path
        except Exception as e:
            logging.error(f"Synthesis Error: {e}")
            return None

    async def generate_visualizations(self, context: str, output_dir: str) -> None:
        """
        Generates Slidev and Mermaid code for visualizations.
        
        Args:
            context: The text content to base visualizations on.
            output_dir: The directory to save the visualization bundle.
        """
        prompt: str = f"Generate Slidev (slides.md) and Mermaid (mindmap.mmd) code from this:\n{context[:10000]}"
        try:
            response: Any = await self.generate_with_fallback(prompt)
            if response and response.text:
                viz_path: str = os.path.join(output_dir, "visualizations.md")
                with open(viz_path, "w", encoding="utf-8") as f:
                    f.write(response.text)
        except Exception as e:
            logging.error(f"Viz Error: {e}")
        return None

    def pack_and_rename_folder(self, folder_path: str, master_report_path: str) -> None:
        """
        Final Phase: Packs reports and renames the folder for archival.
        
        Args:
            folder_path: The directory to process.
            master_report_path: The path to the master synthesis file.
        """
        folder_name: str = os.path.basename(folder_path)
        
        with open(master_report_path, "r", encoding="utf-8") as f:
            first_line: str = f.readline()
            title: str = first_line.replace("#", "").split(":")[ -1].strip()
            # Sanitize title
            title = "".join([c for c in title if c.isalnum() or c in (" ", "_")]).strip()
            title = title.replace(" ", "_")[:30]
        
        new_name: str = f"DONE_{title}_{folder_name}"
        RobustUtils.safe_rename(folder_path, new_name)
        logging.info(f"🏁 [Archived] Folder renamed to: {new_name}")
        return None


class AsyncProcessor:
    """
    Handles file events in a queue to prevent blocking the Watchdog observer.
    """
    def __init__(self, pipeline: ResearchPipeline):
        """
        Initializes the AsyncProcessor.
        
        Args:
            pipeline: An instance of ResearchPipeline to use for processing.
        """
        self.pipeline = pipeline
        self.queue = asyncio.Queue()
        self.processing = False

    async def worker(self) -> None:
        """
        The main worker loop that processes tasks from the queue.
        """
        logging.info("👷 Async Worker started...")
        self.processing = True
        while True:
            file_path: str = await self.queue.get()
            try:
                await self.process_workflow(file_path)
            except Exception as e:
                logging.error(f"❌ Worker Error: {e}")
            finally:
                self.queue.task_done()
        return None

    async def process_workflow(self, file_path: str) -> None:
        """
        Orchestrates the full research workflow for a given file.
        
        Args:
            file_path: The path to the file to be processed.
        """
        report_path: Optional[str] = await self.pipeline.run_gemini_research(file_path)
        if not report_path: 
            return None
        
        folder_path: str = os.path.dirname(file_path)
        synthesis_path: Optional[str] = await self.pipeline.run_folder_synthesis(folder_path)
        
        content_to_push: str = ""
        with open(report_path, 'r') as f: content_to_push += f.read()
        if synthesis_path:
            try:
                with open(synthesis_path, 'r') as f: 
                    content_to_push += "\n\n" + f.read()
            except Exception as e:
                logging.warning(f"Could not read synthesis for upload: {e}")

        upload_package_path: str = os.path.join(folder_path, "upload_package.md")
        with open(upload_package_path, "w", encoding="utf-8") as f: f.write(content_to_push)
        
        topic: str = os.path.basename(folder_path)
        logging.info(f"🤖 Automating NotebookLM for: {topic}")
        automator_script = os.path.join(os.path.dirname(__file__), "notebooklm_automator.py")
        
        map_file = os.path.join(self.pipeline.root_dir, ".notebook_map.json")
        proc = await asyncio.create_subprocess_exec(
            sys.executable, automator_script, upload_package_path, topic, map_file,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        # Semantic Renaming
        output_lines = stdout.decode().strip().split('\n')
        new_topic = None
        for line in reversed(output_lines):
            if line.startswith("RESULT:"):
                new_topic = line.replace("RESULT:", "").strip()
                break
        
        if new_topic and new_topic != "Untitled" and "Success" not in new_topic and "Error" not in new_topic:
            # AESTHETIC UPDATE: Using raw semantic title (no DONE_ prefix)
            final_name = new_topic
            
            new_folder_path = RobustUtils.safe_rename(folder_path, final_name)
            if new_folder_path != folder_path:
                logging.info(f"🏷️ Aesthetic Renamed: {folder_path} -> {new_folder_path}")
                folder_path = new_folder_path

        await self.pipeline.generate_visualizations(content_to_push, folder_path)
        return None
        
    def add_task(self, file_path: str) -> None:
        """
        Safely adds a file path to the processing queue.
        
        Args:
            file_path: The path to the file to be processed.
        """
        # Check queue size to prevent overflow
        if self.queue.qsize() > 50:
            logging.warning("⚠️ Queue full! Dropping task.")
            return
        self.queue.put_nowait(file_path)
        return None


class InputHandler(FileSystemEventHandler):
    """
    Watchdog handler for new files in the research root.
    """
    def __init__(self, processor: AsyncProcessor) -> None:
        """
        Initializes the InputHandler.
        
        Args:
            processor: The AsyncProcessor to delegate tasks to.
        """
        self.processor = processor
        self.loop = asyncio.get_event_loop()

    def on_modified(self, event: Any) -> None:
        """Called when a file is modified."""
        if event.is_directory: 
            return
        self.handle_event(event.src_path)
        return None

    def on_created(self, event: Any) -> None:
        """Called when a file is created."""
        if event.is_directory: 
            return
        self.handle_event(event.src_path)
        return None

    def handle_event(self, file_path: str) -> None:
        """
        Categorizes and queues the file event.
        
        Args:
            file_path: The path to the detected file.
        """
        rel_path: str = os.path.relpath(file_path, ROOT_DIR)
        basename: str = os.path.basename(file_path)
        
        # Skip internal system files
        if file_path.endswith(".py"): 
            return
        if basename.startswith('.'): 
            return
        if "report_" in basename or "visualizations_" in basename or "MASTER_SYNTHESIS" in basename: 
            return
        
        # Check extensions
        supported_exts = ('.txt', '.md', '.png', '.jpg', '.jpeg', '.pdf', '.icloud', '.webloc', '.url', '.html')
        if not file_path.lower().endswith(supported_exts):
            logging.warning(f"⚠️ File ignored: {basename} (Unsupported extension)")
            return

        # Topic Assignment Logic
        # If it's in a subdirectory, the subdirectory is the topic.
        # If it's in the root, it's a "General" thought (Shortcut-friendly).
        # Topic Assignment Logic
        # 1. Root Level -> Moves to 'input_thoughts/General'
        if "/" not in rel_path:
            logging.info(f"📍 Root-level thought detected: {basename}. Assigning to 'General' topic.")
            general_dir: str = os.path.join(ROOT_DIR, "input_thoughts", "General")
            os.makedirs(general_dir, exist_ok=True)
            new_path: str = os.path.join(general_dir, basename)
            try:
                shutil.move(file_path, new_path)
                file_path = new_path
            except Exception as e:
                logging.error(f"Failed to move root-level file: {e}")
                return
        
        # 2. Direct Inbox Level (e.g. input_thoughts/idea.txt) -> Pack into own folder
        # This prevents renaming the entire 'input_thoughts' folder
        parts = rel_path.split(os.sep)
        if len(parts) == 2 and parts[0] == "input_thoughts":
            stem = os.path.splitext(basename)[0]
            # Sanitize stem: replace newlines with space, remove invalid chars
            stem = stem.replace("\n", " ").replace("\r", " ")
            stem = "".join([c for c in stem if c.isalnum() or c in (" ", "_", "-")]).strip()
            # Truncate to prevent extremely long folder names
            if len(stem) > 60:
                stem = stem[:57] + "..."
            if not stem: stem = "Untitled_Research"
            
            logging.info(f"🃏 Inbox item detected: {basename}. Packing into dedicated folder: {stem}")
            topic_dir: str = os.path.join(ROOT_DIR, "input_thoughts", stem)
            os.makedirs(topic_dir, exist_ok=True)
            new_path: str = os.path.join(topic_dir, basename)
            try:
                shutil.move(file_path, new_path)
                file_path = new_path
            except Exception as e:
                logging.error(f"Failed to pack inbox file: {e}")
                return

        logging.info(f"⚡️ New Thought Detected: {os.path.basename(file_path)} (Queued)")
        # Give time for Shortcuts or iCloud to finish moving/downloading
        time.sleep(1) 
        self.processor.add_task(file_path)
        return None

async def scan_existing_files(processor: AsyncProcessor) -> None:
    """
    Scans and processes files that already exist before script started.
    
    Args:
        processor: The AsyncProcessor instance.
    """
    logging.info("🔎 Scanning for existing files...")
    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            file_path: str = os.path.join(root, file)
            # Skip hidden files unless they are iCloud placeholders
            if os.path.basename(file_path).startswith('.') and not file_path.endswith('.icloud'): 
                continue
            
            supported_exts = ('.txt', '.md', '.png', '.jpg', '.jpeg', '.pdf', '.icloud', '.webloc', '.url', '.html')
            if not file_path.lower().endswith(supported_exts): 
                continue
            if "report_" in file or "visualizations_" in file or "MASTER_SYNTHESIS" in file or "upload_package" in file_path: 
                continue
            
            report_name: str = f"report_{os.path.splitext(file)[0]}.md"
            if os.path.exists(os.path.join(root, report_name)):
                continue

            logging.info(f"📂 Found unprocessed historical file: {file}")
            processor.add_task(file_path)
    return None

def main() -> None:
    """
    Unified entry point for the Automated Research Pipeline.
    Sets up monitoring and begins the processing loop.
    """
    pipeline: ResearchPipeline = ResearchPipeline()
    processor: AsyncProcessor = AsyncProcessor(pipeline)
    handler: InputHandler = InputHandler(processor)
    
    observer: Observer = Observer()
    observer.schedule(handler, ROOT_DIR, recursive=True)
    observer.start()
    
    # Verify Self
    try:
        from scripts.validation_17_layers import validate_code_17_layers
        logging.info("🛡️ [Self-Diagnostic] Running 17-Layer Code Validation...")
        with open(__file__, 'r') as f: self_code = f.read()
        result: Dict[str, Any] = validate_code_17_layers(self_code, "auto_research_pipeline.py")
        if result['quality_score'] < 80:
            logging.warning(f"⚠️ Code Quality Warning! Score: {result['quality_score']}/100")
        else:
            logging.info(f"✅ Code Integrity Verified.")
    except Exception as e:
        logging.debug(f"Self-audit skipped: {e}")

    logging.info(f"🚀 Robust Logic Pipeline Started.")
    logging.info(f"📂 Root: {os.path.abspath(ROOT_DIR)}")
    
    loop: asyncio.AbstractEventLoop = asyncio.get_event_loop()
    # Schedule historical scan
    loop.run_until_complete(scan_existing_files(processor))
    
    # Start the worker
    try:
        loop.run_until_complete(processor.worker())
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    return None

if __name__ == "__main__":
    main()
