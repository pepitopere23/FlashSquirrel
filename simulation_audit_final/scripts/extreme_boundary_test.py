#!/usr/bin/env python3
"""
FlashSquirrel Extreme Boundary Test 🐿️💣
Simulates the 'Human Paradox' - weird filenames, corrupted links, and batch stress.
"""
import os
import shutil
import time

TEST_DIR = "input_thoughts/STRESS_TEST_UNIT"

def setup_test():
    if os.path.exists(TEST_DIR):
        shutil.rmtree(TEST_DIR)
    os.makedirs(TEST_DIR, exist_ok=True)

def create_weird_cases():
    print("🔥 Generating Weird Cases...")
    
    # 1. Emoji & Newline Filename
    with open(os.path.join(TEST_DIR, "🐿️\nNewline_Thought.txt"), "w") as f:
        f.write("Testing if filenames with emojis and newlines break the path logic.")
    
    # 2. Corrupted .webloc (Plain Text)
    with open(os.path.join(TEST_DIR, "corrupted_link.webloc"), "w") as f:
        f.write("I am not XML. I am just a confused string.")
        
    # 3. Single Quote & Space
    with open(os.path.join(TEST_DIR, "User's Weird Idea 2026.md"), "w") as f:
        f.write("Testing single quotes in filenames.")
        
    # 4. Massive Batch Attack (Rapid Fire)
    print("⚡️ Simulating 50-file Batch Drop...")
    for i in range(50):
        with open(os.path.join(TEST_DIR, f"batch_task_{i}.txt"), "w") as f:
            f.write(f"Batch item {i}")

    # 5. Nested Evil Path
    evil_inner = os.path.join(TEST_DIR, "Level1", "Level2", "Level3")
    os.makedirs(evil_inner, exist_ok=True)
    with open(os.path.join(evil_inner, "buried_treasure.pdf"), "w") as f:
        f.write("%PDF-1.4 (Fake PDF for path testing)")

if __name__ == "__main__":
    setup_test()
    create_weird_cases()
    print("\n✅ Stress Test Case Generation Complete!")
    print(f"👉 Now run FlashSquirrel and watch the 'STRESS_TEST_UNIT' folder.")
    print("Expected Results:")
    print("- Weird names are handled/escaped.")
    print("- Corrupted links generate RESEARCH_FAILURE.md (Terminal Error).")
    print("- Batch tasks are queued and processed sequentially without dropping.")
