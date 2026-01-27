#!/bin/bash
# 自動啟動腳本：進入專案目錄，啟動虛擬環境並執行主程式
cd "/Users/chenpeijun/research_pipeline"
source .venv/bin/activate
export PYTHONUNBUFFERED=1
python3 scripts/auto_research_pipeline.py >> pipeline_bg.log 2>&1
