#!/usr/bin/env python3
"""
Generate Reports Script
Process raw thought files into structured research reports using Gemini API.
Designed to align with 17-layer validation standards.
"""

import os
import glob
import time
import argparse
from typing import List, Optional, Dict
import google.generativeai as genai
from dotenv import load_dotenv

# 加載環境變數
load_dotenv()

# 設定常數
INPUT_DIR = "raw_thoughts"
OUTPUT_DIR = "processed_reports"
MODEL_NAME = "gemini-1.5-pro-latest"  # Use a valid model name


def setup_directories() -> None:
    """
    Ensure input and output directories exist.
    
    L15: Error handling included (os.makedirs can fail).
    """
    try:
        os.makedirs(INPUT_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    except OSError as e:
        print(f"Error creating directories: {e}")
        raise


def load_raw_files(directory: str) -> List[str]:
    """
    Load all text files from the specified directory.

    Args:
        directory: The directory to search for files.

    Returns:
        List of file paths found.
    """
    try:
        # L16: Avoid shell injection by using glob directly, not passing user input to shell
        files = glob.glob(os.path.join(directory, "*.txt"))
        files.extend(glob.glob(os.path.join(directory, "*.md")))
        return files
    except Exception as e:
        print(f"Error scanning directory {directory}: {e}")
        return []


def generate_report_content(file_content: str, filename: str) -> Optional[str]:
    """
    Call Gemini API to generate a report from raw content.

    Args:
        file_content: The raw text content.
        filename: The original filename for context.

    Returns:
        The generated report markdown, or None if failed.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment.")
        return None

    genai.configure(api_key=api_key)
    
    try:
        model = genai.GenerativeModel(MODEL_NAME)
        
        prompt = f"""
        You are a senior researcher. Please read the following raw notes ({filename}), extract core arguments, 
        add missing context (using your knowledge base), and write a rigorous research report.
        
        The report must contain:
        1. Executive Summary
        2. Key Insights
        3. Data Analysis (if applicable)
        4. Strategic Recommendations
        
        Output format: Markdown.
        
        Raw Content:
        {file_content}
        """
        
        # L15: Error handling for API calls
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"API Error processing {filename}: {e}")
        return None


def save_report(content: str, original_filename: str) -> bool:
    """
    Save the generated report to the output directory.

    Args:
        content: The markdown content to save.
        original_filename: The basename of the original file.

    Returns:
        True if successful, False otherwise.
    """
    try:
        basename = os.path.basename(original_filename)
        name_without_ext = os.path.splitext(basename)[0]
        timestamp = time.strftime("%Y-%m-%d")
        new_filename = f"{timestamp}_{name_without_ext}_Report.md"
        output_path = os.path.join(OUTPUT_DIR, new_filename)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"Saved report to: {output_path}")
        return True
    
    except IOError as e:
        print(f"Error saving file {original_filename}: {e}")
        return False


def process_files(files: List[str]) -> None:
    """
    Process a list of files sequentially.
    
    Args:
        files: List of file paths to process.
    """
    for file_path in files:
        print(f"Processing: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            if not content.strip():
                print(f"Skipping empty file: {file_path}")
                continue
                
            report = generate_report_content(content, os.path.basename(file_path))
            
            if report:
                save_report(report, file_path)
            else:
                print(f"Failed to generate report for {file_path}")
                
            # Rate limit mitigation (simple)
            time.sleep(2) 
            
        except Exception as e:
            print(f"Error reading {file_path}: {e}")


def main() -> None:
    """
    Main entry point for the script.
    """
    parser = argparse.ArgumentParser(description="Batch process thoughts to reports.")
    parser.parse_args()
    
    setup_directories()
    
    files = load_raw_files(INPUT_DIR)
    if not files:
        print(f"No files found in {INPUT_DIR}. Add .txt or .md files to start.")
        return
        
    print(f"Found {len(files)} files to process.")
    process_files(files)


if __name__ == "__main__":
    main()
