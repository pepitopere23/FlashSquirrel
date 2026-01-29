#!/usr/bin/env python3
import os
import sys
import asyncio
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "scripts"))

from scripts.auto_research_pipeline import ResearchPipeline, AsyncProcessor

async def force_research(file_path: str):
    print(f"🚀 Forcing research for: {file_path}")
    pipeline = ResearchPipeline()
    processor = AsyncProcessor(pipeline)
    
    # Run the workflow directly without queue
    await processor.process_workflow(file_path)
    print("✅ Force research completed.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/force_research.py <file_path>")
        sys.exit(1)
    
    target_file = sys.argv[1]
    asyncio.run(force_research(target_file))
