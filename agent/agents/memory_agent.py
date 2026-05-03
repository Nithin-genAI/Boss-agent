# agents/memory_agent.py — Specialist for memory operations
from typing import Dict, Any


class MemoryAgent:
    """
    Handles: storing facts, recalling facts, preferences, task history.
    Bridges to Mem0 / local memory.
    """
    
    def __init__(self, long_term_memory):
        self.ltm = long_term_memory
    
    def execute(self, instruction: str) -> Dict[str, Any]:
        """Handle memory queries."""
        inst_lower = instruction.lower()
        
        # Recall
        if any(k in inst_lower for k in ["what's my", "who am i", "what do i", "remind me", "what was", "do you know", "tell me about"]):
            return self._recall(instruction)
        
        # Store
        if any(k in inst_lower for k in ["my name is", "i like", "i prefer", "i hate", "remember that", "don't forget"]):
            return self._store(instruction)
        
        return {"success": False, "error": "Unknown memory instruction"}
    
    def _recall(self, instruction: str) -> Dict[str, Any]:
        # Check preferences first
        if "name" in instruction.lower():
            name = self.ltm.get_preference("user_name")
            if name:
                return {"success": True, "action": "recall", "fact": f"Your name is {name}"}
        
        # General recall
        facts = self.ltm.recall_facts(instruction, limit=3)
        if facts:
            return {"success": True, "action": "recall", "facts": facts}
        
        return {"success": True, "action": "recall", "fact": "I don't have that information yet."}
    
    def _store(self, instruction: str) -> Dict[str, Any]:
        import re
        
        # Name
        name_match = re.search(r"(?:my name is|i am|call me)\s+([A-Z][a-zA-Z]+)", instruction)
        if name_match:
            name = name_match.group(1)
            self.ltm.store_preference("user_name", name)
            self.ltm.store_fact(f"User's name is {name}", "identity")
            return {"success": True, "action": "store", "stored": f"name = {name}"}
        
        # Likes
        like_match = re.search(r"i like\s+(.+?)(?:\.|$)", instruction.lower())
        if like_match:
            pref = like_match.group(1).strip()
            self.ltm.store_fact(f"User likes {pref}", "preference")
            return {"success": True, "action": "store", "stored": f"likes = {pref}"}
        
        return {"success": True, "action": "store", "stored": "note saved"}
