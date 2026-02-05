import os
import sys
import asyncio
import logging

# Path Fixes for absolute reliability
# Path Fixes for absolute reliability
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_DIR, "scripts"))

try:
    from auto_research_pipeline import AsyncProcessor, StateTracker, ResearchPipeline, ROOT_DIR
except ImportError:
    print("❌ Failed to import pipeline logic. Ensure you are in the correct directory.")
    sys.exit(1)

# Configure standalone logging to console
logging.basicConfig(level=logging.INFO, format='%(asctime)s - ⚡️ [ForceMode] %(message)s')

async def force_process(target_substring):
    print(f"🚀 [Force Pursuit] Searching for files containing: '{target_substring}'")
    
    # Initialize components
    state_file = os.path.join(ROOT_DIR, ".squirrel_state.json")
    state_tracker = StateTracker(state_file)
    pipeline = ResearchPipeline(state_tracker)
    processor = AsyncProcessor(pipeline, state_tracker)
    
    targets = []
    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            if target_substring in file and not file.startswith("report_") and not file.startswith("."):
                targets.append(os.path.join(root, file))
    
    if not targets:
        print(f"⚠️ [Not Found] No files matching '{target_substring}' found in {ROOT_DIR}")
        return

    for target in targets:
        print(f"🔥 [Ignition] Forcing analysis for: {os.path.basename(target)}")
        try:
            # We bypass the queue and call process_workflow directly
            await processor.process_workflow(target)
            print(f"✅ [Success] Analysis complete for: {os.path.basename(target)}")
        except Exception as e:
            print(f"❌ [Error] Failed to process {os.path.basename(target)}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 force_research.py <filename_substring>")
        sys.exit(1)
        
    keyword = sys.argv[1]
    asyncio.run(force_process(keyword))
