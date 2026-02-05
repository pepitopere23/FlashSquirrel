import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

# L16: Singleton / Global Context Manager
class MentalModel:
    """
    FlashSquirrel V31: Semantic Anchoring & Context Tracking
    Tracks user flow to provide 'Mental Context' for ambiguous files.
    """
    def __init__(self, persistence_file: str):
        self.persistence_file = persistence_file
        self.history: List[Dict] = []
        self._load()

    def _load(self):
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
            except Exception as e:
                logging.error(f"🧠 Failed to load Mental Model: {e}")
                self.history = []

    def _save(self):
        try:
            # Prune old entries > 24 hours to keep file small
            cutoff = (datetime.now() - timedelta(hours=24)).isoformat()
            self.history = [h for h in self.history if h['timestamp'] > cutoff]
            
            with open(self.persistence_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"🧠 Failed to save Mental Model: {e}")

    def add_context(self, topic: str):
        """Register a successful topic engagement."""
        # Sanity Check: Don't learn from system folders or debris
        if not topic or topic in ["Resurrected_ICU", "ICU_Salvageable", "Critical_Error", "_QUARANTINE_"]:
            return 

        entry = {
            "topic": topic,
            "timestamp": datetime.now().isoformat()
        }
        self.history.append(entry)
        self._save()

    def get_dominant_context(self, window_minutes: int = 20, threshold: int = 2) -> Optional[str]:
        """
        Returns the dominant topic if >= threshold events occurred in the last window_minutes.
        Threshold lowered to 2 to be more responsive for rapid workflows.
        """
        now = datetime.now()
        cutoff = now - timedelta(minutes=window_minutes)
        
        recent_topics = [
            h['topic'] for h in self.history 
            if datetime.fromisoformat(h['timestamp']) > cutoff
        ]
        
        if not recent_topics:
            return None
            
        # Count usage
        from collections import Counter
        counts = Counter(recent_topics)
        most_common = counts.most_common(1)
        
        if not most_common:
            return None
            
        topic, count = most_common[0]
        
        if count >= threshold:
            logging.info(f"🧠 Mental Model: Dominant Context is '{topic}' ({count} hits in {window_minutes}m)")
            return topic
            
        return None
