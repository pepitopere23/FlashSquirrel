#!/bin/bash

# Configuration
PLIST_LABEL="com.user.research_pipeline"
LOG_FILE="$(cd "$(dirname "$0")/.." && pwd)/pipeline_bg.log"
MAX_LOG_SIZE_MB=50

echo "🏥 Starting System Health Check..."

# 1. check python process
if pgrep -f "auto_research_pipeline.py" > /dev/null; then
    echo "✅ Pipeline Daemon is RUNNING."
else
    echo "❌ Pipeline Daemon is STOPPED."
    echo "🔄 Attempting restart via launchctl..."
    # Attempt to reload if plist exists in LaunchAgents (assuming user installed it)
    if [ -f ~/Library/LaunchAgents/$PLIST_LABEL.plist ]; then
        launchctl unload ~/Library/LaunchAgents/$PLIST_LABEL.plist
        launchctl load ~/Library/LaunchAgents/$PLIST_LABEL.plist
        echo "   Restart signal sent."
    else
        echo "   Warning: Service not installed in ~/Library/LaunchAgents/"
    fi
fi

# 2. Check Log Size
if [ -f "$LOG_FILE" ]; then
    current_size=$(du -m "$LOG_FILE" | cut -f1)
    if [ "$current_size" -gt "$MAX_LOG_SIZE_MB" ]; then
        echo "⚠️ Log file is too large ($current_size MB). Rotating..."
        mv "$LOG_FILE" "$LOG_FILE.old"
        touch "$LOG_FILE"
        echo "   Log rotated."
    else
        echo "✅ Log size is healthy ($current_size MB)."
    fi
else
    echo "⚠️ No log file found."
fi

echo "🏥 Health Check Complete."
