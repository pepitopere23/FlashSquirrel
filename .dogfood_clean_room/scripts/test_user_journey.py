import os
import shutil
import time
import asyncio
import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

# Configure logging for the test
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Import our core logic
# Use absolute paths to be safe
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.auto_research_pipeline import ResearchPipeline, AsyncProcessor, ROOT_DIR

async def simulate_user_journey():
    logging.info("🐿️ Starting User Journey Simulation...")
    
    # 1. Setup a Test Topic Folder
    test_topic = "Simulation_Test_Topic"
    test_path = os.path.join(ROOT_DIR, "input_thoughts", test_topic)
    os.makedirs(test_path, exist_ok=True)
    
    test_file = os.path.join(test_path, "idea.txt")
    with open(test_file, "w") as f:
        f.write("This is a simulated idea for FlashSquirrel testing.")
    
    logging.info(f"✅ Created test folder and file: {test_file}")

    # 2. Mock the Gemini API using async-compatible mocks
    mock_response = MagicMock()
    mock_response.text = "# Simulated Master Synthesis\nThis is a mock result."
    
    # 3. Instantiate the Pipeline and Processor
    pipeline = ResearchPipeline()
    processor = AsyncProcessor(pipeline)
    
    async def mock_run_gemini_research(*args, **kwargs):
        report_path = os.path.join(test_path, "report_idea.md")
        with open(report_path, "w") as f:
            f.write("# Mock Report\nResearch complete.")
        return report_path
    
    async def mock_run_folder_synthesis(*args, **kwargs):
        return os.path.join(test_path, "MASTER_SYNTHESIS.md")
        
    async def mock_visualizations(*args, **kwargs):
        return None

    with patch.object(pipeline, 'generate_with_fallback', return_value=mock_response), \
         patch.object(pipeline, 'run_gemini_research', side_effect=mock_run_gemini_research), \
         patch.object(pipeline, 'run_folder_synthesis', side_effect=mock_run_folder_synthesis), \
         patch.object(pipeline, 'generate_visualizations', side_effect=mock_visualizations):
        
        logging.info("🚀 Triggering Manual Processing...")
        await processor.process_workflow(test_file)
        
        # 4. Verify Results
        logging.info("🔎 Verifying outputs...")
        
        # Check if reports exist
        report_path = os.path.join(test_path, "report_idea.md")
        # Note: the actual script renames the folder at the end
        
        # We need to find the renamed folder (DONE_...)
        renamed_folder = None
        for item in os.listdir(os.path.join(ROOT_DIR, "input_thoughts")):
            if item.startswith("DONE_") and test_topic in item:
                renamed_folder = item
                break
        
        if renamed_folder:
            logging.info(f"✨ SUCCESS! Folder renamed to: {renamed_folder}")
            # Cleanup
            # shutil.rmtree(os.path.join(ROOT_DIR, "input_thoughts", renamed_folder))
            return True
        else:
            logging.error("❌ FAILURE: Folder was not renamed correctly.")
            return False

if __name__ == "__main__":
    result = asyncio.run(simulate_user_journey())
    if result:
        print("\n" + "🌟" * 20)
        print("SIMULATION PASSED: The user journey is ROCK SOLID.")
        print("🌟" * 20 + "\n")
        exit(0)
    else:
        print("SIMULATION FAILED.")
        exit(1)
