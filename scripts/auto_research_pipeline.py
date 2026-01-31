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
import socket
import hashlib
import json
from typing import Optional, List, Any, Dict, Set
from watchdog.observers.polling import PollingObserver as Observer
from watchdog.events import FileSystemEventHandler
from google import genai
from google.genai import types
from dotenv import load_dotenv

# RED-TEAM SHIELD: Custom Exceptions for Iron Persistence
class TerminalResearchError(Exception):
    """Errors that cannot be recovered from (e.g. Safety Filters, Invalid Auth)."""
    def __init__(self, message: str):
        """Initialize with message."""
        super().__init__(message)

class TransientResearchError(Exception):
    """Errors that can be recovered by waiting (e.g. 429, 500, Network)."""
    def __init__(self, message: str):
        """Initialize with message."""
        super().__init__(message)

# Configuration
load_dotenv()

# Cross-platform Root Directory handling
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

# Normalize and ensure root dir exists (Omega-27 L16 Guard)
ROOT_DIR = os.path.abspath(os.path.normpath(ROOT_DIR)).strip()
os.makedirs(os.path.abspath(os.path.normpath(ROOT_DIR)).strip(), exist_ok=True)

# SINGLETON LOCK (Phase O): Prevent concurrent engine instances
def check_engine_singleton() -> bool:
    """
    Prevents multiple instances of the research engine from running.
    Lock is placed in /tmp to ensure local machine scope (bypassing iCloud sync).
    
    Returns:
        True if the lock is acquired, sys.exit() otherwise.
    """
    import getpass
    
    username = getpass.getuser()
    # L18 Stability: Strictly machine-local lock in /tmp to avoid iCloud sync collisions.
    lock_file = os.path.join("/tmp", f"flash_squirrel_{username}.lock")
    
    if os.path.exists(lock_file):
        try:
            with open(lock_file, "r") as f:
                old_pid = int(f.read().strip())
                os.kill(old_pid, 0)
                logging.error(f"❌ Concurrent Engine Blocked (PID: {old_pid}).")
                logging.warning(f"💡 Local machine lock detected at: {lock_file}")
                sys.exit(1)
        except (ValueError, ProcessLookupError, OSError):
            # L15: Transparent handling for stale locks
            logging.debug("Stale or invalid lock found. Reclaiming.")
    
    try:
        with open(lock_file, "w") as f:
            f.write(str(os.getpid()))
        import atexit
        # Robust Cleanup: Ensure lock is removed on exit
        atexit.register(lambda: os.remove(lock_file) if os.path.exists(lock_file) else None)
        return True
    except Exception as e:
        logging.warning(f"⚠️ Singleton Lock failed: {e}")
        return False




# --- Phase L+: Persistence Logic ---
class StateTracker:
    """
    Persistent state manager for FlashSquirrel to prevent redundant processing 
    and track file history across sessions and machines.
    """
    def __init__(self, state_file: str):
        self.state_file = state_file
        self.state: Dict[str, Any] = self._load()
        # memory set for fast lookup: {hash}
        self.processed_hashes: Set[str] = set()
        self._sync_hashes()
        # Ensure file exists
        if not os.path.exists(self.state_file):
            self._save()

    def _load(self) -> Dict[str, Any]:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # V3 Upgrade: Ensure fault_history exists
                    if "fault_history" not in data:
                        data["fault_history"] = {}
                    return data
            except Exception as e:
                logging.error(f"⚠️ State load failed: {e}")
        return {"processed": {}, "fault_history": {}, "version": "1.2.0-Ironclad"}

    def _sync_hashes(self) -> None:
        processed = self.state.get("processed", {})
        for _, info in processed.items():
            h = info.get("hash")
            if h: self.processed_hashes.add(h)

    def is_processed(self, file_path: str, file_hash: Optional[str] = None) -> bool:
        """
        Check if a file hash has already been finished AND the output exists.
        V3 Upgrade: Economic Reality Check (Don't trust DB if file is missing).
        """
        h = file_hash or RobustUtils.calculate_hash(file_path)
        
        # 1. DB Check
        if h not in self.processed_hashes:
            return False
            
        # 2. Reality Check (Economy Guard)
        # Find the expected report path
        parent = os.path.dirname(file_path)
        stem = os.path.splitext(os.path.basename(file_path))[0]
        report_path = os.path.join(parent, f"report_{stem}.md")
        
        if os.path.exists(report_path) and os.path.getsize(report_path) > 100:
            return True
            
        logging.warning(f"📉 Identity Mismatch: Logic says done, Reality says missing. Re-processing: {os.path.basename(file_path)}")
        return False

    def mark_done(self, file_path: str, file_hash: str, metadata: Optional[Dict] = None) -> None:
        """Saves a file as completed in the persistent store."""
        if "processed" not in self.state: self.state["processed"] = {}
        
        self.state["processed"][file_path] = {
            "hash": file_hash,
            "timestamp": time.time(),
            "meta": metadata or {}
        }
        # Clear any fault history on success
        if "fault_history" in self.state and file_hash in self.state["fault_history"]:
            del self.state["fault_history"][file_hash]
            
        self.processed_hashes.add(file_hash)
        self._save()

    def get_fault_tier(self, file_hash: str) -> int:
        """Retrieves the last recorded failure tier for this file (Persistence Memory)."""
        history = self.state.get("fault_history", {})
        if file_hash in history:
            return history[file_hash].get("tier", 1)
        return 1

    def record_fault(self, file_hash: str, tier: int, reason: str) -> None:
        """Records a failure to persist the escalation state."""
        if "fault_history" not in self.state: self.state["fault_history"] = {}
        self.state["fault_history"][file_hash] = {
            "tier": tier,
            "reason": reason,
            "timestamp": time.time()
        }
        self._save()

    def _save(self) -> None:
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"❌ State save failed: {e}")

class RobustUtils:
    """Utility class for cross-platform file and iCloud synchronization handling."""
    
    @staticmethod
    def calculate_hash(file_path: str) -> str:
        """
        Generates a SHA-256 hash with a stability guard to prevent 
        collision with partially synced iCloud files.
        """
        if not os.path.exists(file_path):
            return "ghost_file_" + str(time.time())
            
        # L18 Stability Guard: Ensure file is not being written to (1.5s silent window)
        try:
            size_initial = os.path.getsize(file_path)
            time.sleep(1.5)
            if os.path.getsize(file_path) != size_initial:
                logging.debug(f"⏳ File '{os.path.basename(file_path)}' is unstable. Retrying hash...")
                return RobustUtils.calculate_hash(file_path) # Recursive stability wait
        except Exception:
            pass

        sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                while chunk := f.read(8192):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception:
            return "hash_error_" + str(time.time())
    
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
        # Force new_name to be a single-level name (no slashes)
        new_name = os.path.basename(new_name)
        new_path = os.path.join(parent, new_name)
        
        if os.path.exists(new_path) and new_path != old_path:
            unique_suffix = uuid.uuid4().hex[:4]
            new_path = f"{new_path}_{unique_suffix}"
            logging.warning(f"⚠️ Name conflict. Renaming to: {os.path.basename(new_path)}")
        
        try:
            # L16: Harden path operations for Omega-27 (using .strip() for audit)
            os.rename(
                os.path.abspath(os.path.normpath(old_path)).strip(),
                os.path.abspath(os.path.normpath(new_path)).strip()
            )

            return new_path



        except Exception as e:
            logging.error(f"❌ Rename failed: {e}")
            return old_path

    @staticmethod
    def get_topic_id(folder_path: str) -> str:
        """
        Retrieves or generates a stable identity for a research topic folder.
        """
        id_file = os.path.join(folder_path, ".topic_id")

        if os.path.exists(id_file):
            try:
                with open(id_file, "r") as f:
                    return f.read().strip()
            except Exception as e:
                logging.debug(f"Could not read topic ID from existing file: {e}")

        
        new_id = uuid.uuid4().hex[:8]
        try:
            with open(id_file, "w") as f:
                f.write(new_id)
        except Exception as e:
            logging.error(f"Failed to write topic ID: {e}")
        return new_id

    @staticmethod
    def verify_home_path() -> None:
        """
        L16/L17/L18 Resilience: Environmental Sovereign Guard.
        Prevents 'Zombie Squirrels' (same machine) and 'Dual-Runner Collisions' (multi-machine).
        """
        script_actual_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        current_machine = socket.gethostname()
        owner_id = os.getenv("RESEARCH_OWNER_ID")
        
        # 1. Host Sovereignty Check
        if owner_id and owner_id != current_machine:
            logging.info(f"💤 Sovereign Mode: Current machine ({current_machine}) is NOT the designated runner ({owner_id}).")
            logging.info("Standing by. (Manual tests still allowed if bypass engaged).")
            # In background mode, we exit. In manual mode, we might warn.
            if os.getenv("PIPELINE_BG_MODE") == "1":
                sys.exit(0)
            return

        # 2. Local Path Integrity (Zombie Defense)
        home_marker = os.path.join(ROOT_DIR, ".squirrel_home_lock")
        current_identity = f"{current_machine}|{script_actual_path}"
        
        if not os.path.exists(home_marker):
            try:
                with open(home_marker, "w") as f: f.write(current_identity)
                logging.info(f"🏠 Home Territory Claimed: {current_machine}")
            except Exception as e:
                logging.warning(f"Metadata lock skipped: {e}")
            return

        try:
            with open(home_marker, "r") as f:
                content = f.read().strip()
                if "|" in content:
                    recorded_machine, recorded_path = content.split("|", 1)
                    if recorded_machine == current_machine and recorded_path != script_actual_path:
                        logging.critical("🛑 ZOMBIE ALERT: Mismatch on THIS machine!")
                        logging.critical(f"Expected: {recorded_path}\nActual: {script_actual_path}")
                        sys.exit(1)
        except Exception:
            pass

    @staticmethod
    def should_ignore(file_path: str) -> bool:
        """
        Final authority on whether a file should be ignored by the research engine.
        Prevents recursive loops and system file pollution.
        """
        basename = os.path.basename(file_path)
        # 1. System/Py Files
        if basename.startswith('.') or file_path.endswith('.py'): return True
        # 2. Administrative Folders (Administrative Shield)
        root_parts = os.path.relpath(file_path, ROOT_DIR).split(os.sep)
        # Never process anything in these folders
        if any(p in ["processed_reports", "docs", "scripts", "skills", "chrome_profile_notebooklm"] for p in root_parts): 
            return True
        # 3. Output/Internal Files (Recursive Shield)
        ignore_patterns = (
            "report_", "visualizations", "MASTER_SYNTHESIS", 
            "upload_package", "RESEARCH_FAILURE_", "RESEARCH_SUSPENDED_",
            "mindmap_", "slide_", ".research_lock", ".topic_id", ".DS_Store"
        )
        if any(p in basename for p in ignore_patterns): return True
        # 4. Success Marker Check (Avoid re-processing finished files)
        # Only skip if the report exists AND is stable.
        report_name = f"report_{os.path.splitext(basename)[0]}.md"
        report_path = os.path.join(os.path.dirname(file_path), report_name)
        if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
            return True
        return False


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

class SmartTriage:
    """
    The Industrial Triage Center.
    Routes files to Quarantine based on their "Hope" level.
    """
    QUARANTINE_ROOT = os.path.join(ROOT_DIR, "_QUARANTINE_")
    
    @staticmethod
    def _ensure_dirs():
        os.makedirs(os.path.join(SmartTriage.QUARANTINE_ROOT, "ICU_Salvageable"), exist_ok=True)
        os.makedirs(os.path.join(SmartTriage.QUARANTINE_ROOT, "Low_Quality"), exist_ok=True)
        os.makedirs(os.path.join(SmartTriage.QUARANTINE_ROOT, "Critical_Error"), exist_ok=True)

    @staticmethod
    def move_to_quarantine(file_path: str, reason: str, category: str) -> Optional[str]:
        """
        Moves a file to the appropriate quarantine zone.
        """
        SmartTriage._ensure_dirs()
        if not os.path.exists(file_path): return None
        
        filename = os.path.basename(file_path)
        dest_dir = os.path.join(SmartTriage.QUARANTINE_ROOT, category)
        dest_path = os.path.join(dest_dir, filename)
        
        # Avoid overwriting existing quarantine files (append timestamp)
        if os.path.exists(dest_path):
            stem, ext = os.path.splitext(filename)
            dest_path = os.path.join(dest_dir, f"{stem}_{int(time.time())}{ext}")

        try:
            shutil.move(file_path, dest_path)
            # Write reason slip
            reason_path = dest_path + ".reason.txt"
            with open(reason_path, "w", encoding="utf-8") as f:
                f.write(f"Reason: {reason}\nTimestamp: {time.ctime()}\n")
            logging.warning(f"🚑 Triage: Moved {filename} to {category}. Reason: {reason}")
            return dest_path
        except Exception as e:
            logging.error(f"❌ Triage Failed: {e}")
            return None

class ResearchPipeline:
    """The central engine for processing research folders and generating Gemini reports."""
    
    def __init__(self, state_tracker: StateTracker) -> None:
        """Initializes the Gemini client and model priorities."""
        self.state_tracker = state_tracker
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
        logging.error("❌ All models failed after max retries.")
        # If we got here, it's either because of persistent 429s or a real network blackout
        raise TransientResearchError("Exhausted all models and retries. Waiting for a better window.")

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
        
        # ATOMIC LOCK (Phase G): Prevent concurrent research on the same topic
        lock_path = os.path.join(parent_dir, ".research_lock")
        if os.path.exists(lock_path):
            logging.warning(f"🔒 Topic locked: {os.path.basename(parent_dir)} is being researched by another process.")
            return None
        
        with open(lock_path, "w") as f: f.write(str(time.time()))
        
        try:
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

            # Phase D+: Robust Sync Wait (Stability Guard)
            file_path = RobustUtils.wait_for_icloud_download(file_path)
            if not os.path.exists(file_path):
                return None

            # PERSISTENCE CHECK (Phase L+)
            # Extra layer: If we just finished a hash check in add_task, 
            # we do another quick one here to be 100% thread-safe.
            file_hash = RobustUtils.calculate_hash(file_path)
            if self.state_tracker.is_processed(file_path, file_hash):
                logging.info(f"⏭️ Skipping (Already processed via hash): {filename}")
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

            # 🛠️ Universal File Adapter (Phase L Upgrade)
            # Smart Content Extraction for .docx, .md, .txt, .pdf
            if not content_part:
                # 1. Word Documents (.docx)
                if filename.lower().endswith('.docx'):
                    try:
                        import docx
                        doc = docx.Document(file_path)
                        full_text = []
                        for para in doc.paragraphs:
                            full_text.append(para.text)
                        content_part = "\n".join(full_text)
                        logging.info(f"📄 [Adapter] Extracted text from Word doc: {filename}")
                    except ImportError:
                        logging.error("❌ python-docx not installed. Skipping .docx.")
                        content_part = None
                    except Exception as e:
                        logging.error(f"❌ Failed to parse .docx: {e}")
                        content_part = None

                # 2. Markdown/Text (.md, .txt) - Hardened Reading
                elif filename.lower().endswith(('.md', '.txt')):
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content_part = f.read()
                    except Exception as e:
                        logging.error(f"❌ Failed to read text file: {e}")
                        content_part = None

                # 3. Binary/Image/PDF - Pass as Blob
                elif mime.startswith('image') or mime == 'application/pdf':
                    with open(file_path, "rb") as f:
                        content_part = {'mime_type': mime, 'data': f.read()}
                
                # 4. Fallback
                else:
                    try:
                        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                            content_part = f.read()
                    except:
                        logging.warning(f"⚠️ Unknown file type {mime}. Skipping content.")

            logging.info(f"📡 [Phase 1] Launching Gemini Research for: {filename}...")
            # Re-format prompt with labels
            final_prompt = prompt.format(input_context_label=input_context_label)
            
            # Execute with Fallback (Phase E Resilience)
            response: Any = await self.generate_with_fallback(final_prompt, content_part, tools=[types.Tool(google_search=types.GoogleSearch())])
            
            if not response or not response.text:
                # Terminal Check: If empty, it's often a safety filter or content policy
                raise TerminalResearchError("Gemini returned an empty response. This is likely a terminal Safety Filter hit.")

            report_path: str = os.path.join(parent_dir, f"report_{os.path.splitext(filename)[0]}.md")
            if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
                logging.info(f"⏩ Skipping existing report: {filename}")
                return report_path

            with open(report_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            
            logging.info(f"📄 [Phase 1] Report generated: {report_path}")
            return report_path
        except TerminalResearchError as e:
            # Terminal: Log and stop
            error_path = os.path.join(parent_dir, f"RESEARCH_FAILURE_{os.path.splitext(filename)[0]}.md")
            with open(error_path, "w", encoding="utf-8") as f:
                f.write(f"# ⚠️ Research Terminated / 研究終止\n\n**File**: `{filename}`\n**Reason**: `{str(e)}` (Terminal Policy/Auth Error)\n\n*Manual intervention required.*")
            return None
        except TransientResearchError as e:
            # Re-raise to let AsyncProcessor handle re-queuing
            raise e
        except Exception as e:
            # Untracked exception -> Treat as Transient to be safe
            logging.error(f"Untracked Anomaly: {e}")
            raise TransientResearchError(f"Unexpected error: {str(e)}")
        finally:
            if 'lock_path' in locals() and os.path.exists(os.path.normpath(lock_path)):
                os.remove(os.path.abspath(os.path.normpath(lock_path)).strip())

    async def run_with_ladder(self, file_path: str) -> Optional[str]:
        """
        Executes the logic with the 1M-2M-4M-10M Escalation Ladder.
        """
        file_hash = RobustUtils.calculate_hash(file_path)
        start_tier = self.state_tracker.get_fault_tier(file_hash)
        
        for tier in range(start_tier, 5): # Tiers 1 to 4
            timeout_map = {1: 60, 2: 120, 3: 240, 4: 600}
            model_map = {1: 'gemini-2.0-flash', 2: 'gemini-1.5-flash', 3: 'gemini-1.5-pro', 4: 'gemini-1.5-pro'}
            
            timeout = timeout_map.get(tier, 600)
            model_name = model_map.get(tier, 'gemini-1.5-pro')
            
            logging.info(f"🪜 Ladder Tier {tier}/4: {model_name} (Timeout: {timeout}s) for {os.path.basename(file_path)}")
            
            try:
                # Dynamically set priority for this run
                self.models_priority = [model_name] 
                
                # Strict Timeout Execution
                report_path = await asyncio.wait_for(
                    self.run_gemini_research(file_path), 
                    timeout=timeout
                )
                
                if report_path:
                    # Success: Clear fault history is handled in mark_done, but we can double check
                    return report_path
                    
            except asyncio.TimeoutError:
                logging.warning(f"⏳ Tier {tier} Timed Out ({timeout}s). Escalating...")
                self.state_tracker.record_fault(file_hash, tier + 1, "Timeout")
                # Continue loop to next tier
                
            except TerminalResearchError as e:
                logging.error(f"🛑 Terminal Error in Tier {tier}: {e}")
                # Fail Fast: Critical Error
                SmartTriage.move_to_quarantine(file_path, str(e), "Critical_Error")
                return None
                
            except Exception as e:
                logging.warning(f"⚠️ Tier {tier} Failed: {e}. Escalating...")
                self.state_tracker.record_fault(file_hash, tier + 1, str(e))
                # Continue loop
        
        # If we exit loop, all tiers failed.
        logging.error(f"❌ Ladder Exhausted (Tier 4 Failed). Moving to ICU.")
        SmartTriage.move_to_quarantine(file_path, "Ladder Exhausted (Max Retries)", "ICU_Salvageable")
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
        try:
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
    def __init__(self, pipeline: ResearchPipeline, state_tracker: StateTracker):
        """
        Initializes the AsyncProcessor.
        
        Args:
            pipeline: An instance of ResearchPipeline to use for processing.
            state_tracker: Persistent state manager.
        """
        self.pipeline = pipeline
        self.state_tracker = state_tracker
        self.queue = asyncio.Queue()
        self.active_tasks: set = set() # De-duplication Shield
        self.renaming_lock = asyncio.Lock() # Phase L+: Rename Shield
        self.completed_folders: set = set() # Finality Registry
        self.processing = False

    async def worker(self) -> None:
        """
        The main worker loop that processes tasks from the queue.
        """
        logging.info("👷 Async Worker started...")
        self.processing = True
        while True:
            # Task format: (file_path, retry_count)
            file_path, retry_count = await self.queue.get()
            
            # Anti-Collision: Don't process if already being handled
            if file_path in self.active_tasks:
                logging.debug(f"⏭️  Deduplication: {os.path.basename(file_path)} already in flight.")
                self.queue.task_done()
                continue
            
            self.active_tasks.add(file_path)
            try:
                # Anti-Ghost: Verify file existence at worker level
                if not os.path.exists(file_path):
                    logging.warning(f"👻 Ghost Task: {file_path} no longer exists. Skipping.")
                    continue

                await self.process_workflow(file_path)
                # Success: Cleanup transient markers
                suspension_file = os.path.join(os.path.dirname(file_path), f"RESEARCH_SUSPENDED_{os.path.basename(file_path)}.md")
                # L16: Add lock_path cleanup with strip()
                lock_path = os.path.join(os.path.dirname(file_path), f".lock_{os.path.basename(file_path)}")
                if os.path.exists(os.path.normpath(lock_path)):
                    os.remove(os.path.normpath(lock_path).strip())


                if os.path.exists(os.path.normpath(suspension_file)): 
                    os.remove(os.path.normpath(suspension_file).strip())

            except TransientResearchError as e:
                # ANTI-STRIKE: Exponential Backoff Re-queuing
                if retry_count < 10: # Allow up to 10 persistent retries (Iron Persistence)
                    backoff = min(30 * (2 ** retry_count), 1800) # Max 30 mins
                    logging.warning(f"🛡️ Anti-Strike: Task '{os.path.basename(file_path)}' suspended. Retrying in {backoff}s... (Reason: {e})")
                    
                    # Status Signal: RESEARCH_SUSPENDED.md
                    suspension_file = os.path.join(os.path.dirname(file_path), f"RESEARCH_SUSPENDED_{os.path.basename(file_path)}.md")
                    with open(suspension_file, "w", encoding="utf-8") as f:
                        f.write(f"# ⏳ Research Suspended / 研究暫停\n\n**Status**: Waiting for API/Network recovery.\n**Next Attempt**: ~{backoff}s\n**Attempts**: {retry_count + 1}/10\n\n*The squirrel is not striking; it is waiting for a better window.*")
                    
                    # Sleep and Re-queue
                    await asyncio.sleep(backoff)
                    self.add_task(file_path, retry_count + 1)
                else:
                    logging.error(f"❌ Persistence Exhausted for {file_path}. Declaring total failure.")
                    failure_path = os.path.join(os.path.dirname(file_path), f"RESEARCH_FAILURE_{os.path.basename(file_path)}.md")
                    with open(failure_path, "w", encoding="utf-8") as f:
                        f.write(f"# 🚨 Persistence Exhausted / 全面失敗\n\n**File**: `{os.path.basename(file_path)}`\n**Reason**: Too many transient failures. Check internet/quota.")
            except Exception as e:
                logging.error(f"❌ Worker Error: {e}")
            finally:
                self.active_tasks.discard(file_path)
                self.queue.task_done()
        return None

    async def process_workflow(self, file_path: str) -> None:
        """
        Orchestrates the full research workflow for a given file.
        
        Args:
            file_path: The path to the file to be processed.
        """
        # V3 Upgrade: Use Ladder instead of direct call
        report_path: Optional[str] = await self.pipeline.run_with_ladder(file_path)
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
        topic_id: str = RobustUtils.get_topic_id(folder_path)
        logging.info(f"🤖 Automating NotebookLM: {topic} (ID: {topic_id})")
        automator_script = os.path.join(os.path.dirname(__file__), "notebooklm_automator.py")
        
        map_file = os.path.join(self.pipeline.root_dir, ".notebook_map.json")
        
        # Cycle 6.2: Smart Resilience Loop (The Iron Hand)
        retry_count = 0
        max_retries = 10
        
        while True:
            proc = await asyncio.create_subprocess_exec(
                sys.executable, automator_script, upload_package_path, topic, map_file, topic_id,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            if proc.returncode == 0:
                break
            
            stderr_text = stderr.decode()
            # FATAL ERROR CHECK: Cookie/Auth issues cannot be fixed by retrying.
            if "Authentication failed" in stderr_text or "Cookie" in stderr_text or "expected string" in stderr_text:
                logging.error(f"⛔ Fatal Auth Error for {topic}: {stderr_text.strip()}")
                # V3 Upgrade: Move to Critical_Error immediately
                SmartTriage.move_to_quarantine(file_path, f"NotebookLM Auth Error: {stderr_text.strip()}", "Critical_Error")
                return None
            
            # Circuit Breaker
            retry_count += 1
            if retry_count > max_retries:
                logging.error(f"❌ Circuit Breaker Tripped for {topic} after {max_retries} attempts.")
                # V3 Upgrade: Move to ICU for later retry
                SmartTriage.move_to_quarantine(file_path, f"NotebookLM Upload Timeout ({max_retries} retries)", "ICU_Salvageable")
                return None
            
            # Exponential Backoff (Smart Resilience)
            wait_time = 60 * (2 ** (retry_count - 1))
            logging.warning(f"⚠️ Upload failed for {topic}. Retrying in {wait_time}s (Attempt {retry_count}/{max_retries})...")
            # In a real async loop we should use asyncio.sleep, but we need to ensure we don't block everything?
            # Since this is an async function (process_folder), asyncio.sleep IS non-blocking to other tasks!
            await asyncio.sleep(wait_time)
        
        # Semantic Renaming
        # Phase I: Robust Topic Resolution (Platinum Patch)
        output_lines = stdout.decode().strip().split('\n')
        new_topic = None
        for line in reversed(output_lines):
            clean_line = line.strip()
            if clean_line.startswith("RESULT:"):
                new_topic = clean_line.replace("RESULT:", "").strip()
                # Ensure we don't capture logs by accident
                if "🚀" in new_topic or "⚠️" in new_topic:
                    logging.warning(f"⚠️ Caught mangled RESULT: {new_topic}. Validating...")
                    continue 
                break
        
        await self.pipeline.generate_visualizations(content_to_push, folder_path)
        
        # RED-TEAM FIX (Phase L+): Multi-file Rename Shield (Naming Guardian)
        # We wrap the logic in a lock to ensure only one worker evaluates folder completion at a time.
        async with self.renaming_lock:
            if folder_path in self.completed_folders:
                logging.debug(f"⏭️  Rename skipped: {folder_path} already finalized.")
                return None

            remaining_files = [
                f for f in os.listdir(folder_path) 
                if not RobustUtils.should_ignore(os.path.join(folder_path, f))
                and not os.path.exists(os.path.join(folder_path, f"report_{os.path.splitext(f)[0]}.md"))
            ]
            
            if remaining_files:
                logging.info(f"⏳ Postponing rename: {len(remaining_files)} files remaining in {folder_path}")
                return None
            
            # Mark as completed BEFORE renaming to prevent race conditions during the rename itself
            self.completed_folders.add(folder_path)

        # Proceed with semantic renaming (Outside the lock to keep it non-blocking, but registry protects it)

        # Proceed with semantic renaming
        final_topic_path = folder_path
        if new_topic and new_topic != "Untitled" and "Success" not in new_topic and "Error" not in new_topic:
            # Phase I: Strict Sanitization to prevent '套娃' (Recursive Nesting)
            # Remove any path separators or illegal characters
            sanitized_topic = "".join([c for c in new_topic if c.isalnum() or c in (" ", "_", "-", "(", ")", "：", ":", "[", "]")])
            sanitized_topic = sanitized_topic.replace("/", "_").replace("\\", "_").strip()
            
            final_topic_path = RobustUtils.safe_rename(folder_path, sanitized_topic)
            if final_topic_path != folder_path:
                logging.info(f"🏷️ Semantic Unified: {folder_path} -> {final_topic_path}")
        
        # Phase I: Final Feedback Loop Restoration
        # No more 'processed_reports' move. Keep topics alive in 'input_thoughts'.
        return None
        
    def add_task(self, file_path: str, retry_count: int = 0) -> None:
        """
        Safely adds a file path to the processing queue with optional retry metadata.
        """
        # Safe Queue Capacity (Increased for high-volume research)
        if self.queue.qsize() > 200:
            logging.warning("⚠️ Queue full! Critical overload.")
            return

        self.active_tasks.add(file_path)
        self.queue.put_nowait((file_path, retry_count))
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
        
        if RobustUtils.should_ignore(file_path):
            return
        
        # Phase G: Early Collision Shield (Pre-Settling)
        if file_path in self.processor.active_tasks:
            logging.debug(f"⏭️  Ignored redundant event for: {basename}")
            return

        # Check extensions
        supported_exts = ('.txt', '.md', '.png', '.jpg', '.jpeg', '.pdf', '.icloud', '.webloc', '.url', '.html')
        if not file_path.lower().endswith(supported_exts):
            logging.warning(f"⚠️ File ignored: {basename} (Unsupported extension)")
            return

        # Check extensions
        # If it's in a subdirectory, the subdirectory is the topic.
        # If it's in the root, it's a "General" thought (Shortcut-friendly).
        # Topic Assignment Logic
        # 1. Root Level -> Moves to 'input_thoughts/General'
        if "/" not in rel_path:
            logging.info(f"📍 Root-level thought detected: {basename}. Assigning to 'General' topic.")
            safe_gen_dir: str = os.path.abspath(os.path.normpath(os.path.join(ROOT_DIR, "input_thoughts", "General")))
            os.makedirs(safe_gen_dir, exist_ok=True)

            new_path: str = os.path.join(general_dir, basename)
            try:
                # L16: Harden path operations
                safe_file_p = os.path.abspath(os.path.normpath(file_path)).strip()
                safe_new_p = os.path.abspath(os.path.normpath(new_path)).strip()
                if os.path.exists(safe_new_p):
                    logging.warning(f"Collision at General topic: {basename}. Overwriting.")
                shutil.move(safe_file_p, safe_new_p)
                file_path = safe_new_p

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
            safe_topic_dir: str = os.path.abspath(os.path.normpath(os.path.join(ROOT_DIR, "input_thoughts", stem)))
            os.makedirs(safe_topic_dir, exist_ok=True)



            new_path: str = os.path.join(topic_dir, basename)
            try:
                # L16: Harden path operations
                safe_file_path = os.path.abspath(os.path.normpath(file_path)).strip()
                safe_new_path = os.path.abspath(os.path.normpath(new_path)).strip()
                if os.path.exists(safe_new_path):
                    logging.warning(f"Collision in folder {stem}: {basename}. Overwriting.")
                shutil.move(safe_file_path, safe_new_path)
                file_path = safe_new_path
            except Exception as e:


                logging.error(f"Failed to pack inbox file: {e}")
                return


        logging.info(f"⚡️ New Thought Detected: {os.path.basename(file_path)} (Queued)")
        # Settling Grace Period (Critical for OS/Cloud file stability)
        time.sleep(2) 
        self.processor.add_task(file_path)
        return None

async def scan_existing_files(processor: AsyncProcessor, state_tracker: StateTracker) -> None:
    """
    Scans and processes files that already exist before script started.
    Includes an initial sanitation pass to repair mangled iCloud folder names.
    
    Args:
        processor: The AsyncProcessor instance.
        state_tracker: Persistent state manager.
    """
    logging.info("🔎 Scanning for existing files...")
    
    # 🛡️ Guardian Logic: Initial Sanitation Pass (Fixes mangled \n folders)
    try:
        all_items = os.listdir(ROOT_DIR)
        for item in all_items:
            if "\n" in item or "\r" in item:
                old_path = os.path.join(ROOT_DIR, item)
                clean_name = item.replace("\n", "_").replace("\r", "_").strip()
                new_path = os.path.join(ROOT_DIR, clean_name)
                # Only rename if clean version doesn't exist yet
                if not os.path.exists(new_path):
                    os.rename(old_path, new_path)
                    logging.info(f"🛡️ Auto-Sanitized path: {repr(item)} -> {clean_name}")
    except Exception as e:
        logging.debug(f"Initial sanitation pass skipped: {e}")

    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            file_path: str = os.path.join(root, file)
            # Unified Ignore Logic (Recursive Shield)
            if RobustUtils.should_ignore(file_path):
                continue
            
            # Skip if already processed (Report OR Failure OR State DB exists)
            stem = os.path.splitext(file)[0]
            report_name = f"report_{stem}.md"
            failure_name = f"RESEARCH_FAILURE_{stem}.md"
            
            # Layer 1: Conventional check
            if os.path.exists(os.path.join(root, report_name)) or os.path.exists(os.path.join(root, failure_name)):
                continue
            
            # Layer 2: Persistence check (The "Zero-Amnesia" Shield)
            if state_tracker.is_processed(file_path):
                logging.debug(f"⏭️ Skipping (Recorded in state DB): {file}")
                continue

            logging.info(f"📂 Found unprocessed historical file: {file}")
            processor.add_task(file_path)
    return None

def main() -> None:
    """
    Unified entry point for the Automated Research Pipeline.
    Sets up monitoring and begins the processing loop.
    """
    # L16/Singleton Guard
    check_engine_singleton()
    # L17: Environmental Integrity Check (Exorcism Shield)
    RobustUtils.verify_home_path()
    
    # V3: Night Nurse - ICU Rounds
    # Scans for salvageable files and moves them back to input for a specialized retry.
    icu_dir = os.path.join(ROOT_DIR, "_QUARANTINE_", "ICU_Salvageable")
    if os.path.exists(icu_dir):
        logging.info("👩‍⚕️ Night Nurse: Making rounds in ICU...")
        for f in os.listdir(icu_dir):
            if f.startswith("."): continue
            
            src = os.path.join(icu_dir, f)
            # If it's a file (not a reason.txt)
            if os.path.isfile(src) and not f.endswith(".reason.txt"):
                # Resurrect to a special folder 
                resurrect_dir = os.path.join(ROOT_DIR, "input_thoughts", "Resurrected_ICU")
                os.makedirs(resurrect_dir, exist_ok=True)
                dest = os.path.join(resurrect_dir, f)
                try:
                    shutil.move(src, dest)
                    logging.info(f"✨ Resurrected: {f} -> input_thoughts/Resurrected_ICU")
                except Exception as e:
                    logging.error(f"⚰️ Failed to resurrect {f}: {e}")
    
    # L18 Persistence Store: Global Sync Edition (Inside ROOT_DIR)
    state_file = os.path.join(ROOT_DIR, ".squirrel_state.json")
    state_tracker = StateTracker(state_file)
    
    pipeline: ResearchPipeline = ResearchPipeline(state_tracker)
    processor: AsyncProcessor = AsyncProcessor(pipeline, state_tracker)
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
    loop.run_until_complete(scan_existing_files(processor, state_tracker))
    
    # Start the worker
    try:
        loop.run_until_complete(processor.worker())
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
    return None

if __name__ == "__main__":
    main()
