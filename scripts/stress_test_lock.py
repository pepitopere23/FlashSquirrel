
import os
import time
import fcntl
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - 🔒 [StressTest] - %(message)s')

# Target directory monitored by pipeline
# Target directory monitored by pipeline
# Dynamic Root
ROOT_DIR = os.path.join(os.path.expanduser("~"), "Library", "Mobile Documents", "com~apple~CloudDocs", "研究工作流")
if not os.path.exists(ROOT_DIR):
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGET_DIR = os.path.join(ROOT_DIR, "input_thoughts", "Stress_Test_Zone")
os.makedirs(TARGET_DIR, exist_ok=True)

TEST_FILE = os.path.join(TARGET_DIR, "STRESS_IMG_001.png")

# Use a real image to ensure it triggers the binary path
REAL_IMG_SOURCE = os.path.join(ROOT_DIR, "_QUARANTINE_", "ICU_Salvageable", "IMG_4528.png")

def simulate_icloud_lock():
    if not os.path.exists(REAL_IMG_SOURCE):
        logging.error("Source image not found for test.")
        return

    logging.info(f"1. Creating test file: {TEST_FILE}")
    shutil.copy2(REAL_IMG_SOURCE, TEST_FILE)
    
    logging.info("2. Simulating iCloud Sync Lock (Exclusive Lock)...")
    try:
        # Open and lock the file
        with open(TEST_FILE, "r+b") as f:
            # Apply exclusive lock (mimics iCloud syncing)
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            logging.info("   >>> FILE LOCKED. Holding for 15 seconds...")
            
            # Hold lock for 15s (longer than pipeline's 5s retry)
            for i in range(15):
                time.sleep(1)
                if i % 5 == 0:
                    logging.info(f"   ... locked for {i}s")
            
            logging.info("   <<< RELEASING LOCK.")
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
            
        logging.info("3. Lock released. Pipeline should have succeeded or failed by now.")
        
    except Exception as e:
        logging.error(f"Test failed: {e}")

if __name__ == "__main__":
    simulate_icloud_lock()
