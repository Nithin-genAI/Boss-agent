# memory/long_term.py — Persistent Memory (Mem0 Platform + Local Fallback)
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

# Mem0 SDK
try:
    from mem0 import MemoryClient
    MEM0_AVAILABLE = True
except ImportError:
    MEM0_AVAILABLE = False


class LongTermMemory:
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.mem0_api_key = "m0-jgxM4BqK37MS8Hp5jZGqNVzTGBvw8vchH3BP5ods"
        self.local_file = f"boss_memory_{user_id}.json"
        
        # Local fallback storage (always maintained as backup)
        self.local_memory = self._load_local()
        
        # Initialize Mem0 client
        self.mem0_client = None
        if MEM0_AVAILABLE and self.mem0_api_key:
            try:
                self.mem0_client = MemoryClient(api_key=self.mem0_api_key)
                print(f"   🧠 Long-term memory: Mem0 Platform connected ✅")
            except Exception as e:
                print(f"   ⚠️  Mem0 init failed, using local fallback: {e}")
        else:
            print(f"   🧠 Long-term memory: Local JSON mode ({self.local_file})")
    
    # ─── Core Storage Methods ─────────────────────────────
    
    def store_fact(self, fact: str, category: str = "general"):
        """Store a learned fact about the user or world"""
        # Store to Mem0 Platform
        if self.mem0_client:
            try:
                messages = [
                    {"role": "user", "content": fact}
                ]
                self.mem0_client.add(messages, user_id=self.user_id, metadata={"category": category})
                print(f"   💾 Mem0: Stored fact → '{fact[:60]}...'")
            except Exception as e:
                print(f"   ⚠️  Mem0 store failed: {e}")
        
        # Always store locally as backup
        entry = {
            "type": "fact",
            "content": fact,
            "category": category,
            "timestamp": datetime.now().isoformat()
        }
        self._local_store(entry)
        return True
    
    def recall_facts(self, query: str, limit: int = 5) -> List[str]:
        """Retrieve relevant facts based on query using Mem0 semantic search"""
        # Try Mem0 first (semantic search)
        if self.mem0_client:
            try:
                results = self.mem0_client.search(
                    query,
                    filters={"user_id": self.user_id},
                    limit=limit
                )
                # Mem0 v2 returns a list directly or dict with 'results' key
                memories_list = results if isinstance(results, list) else results.get("results", [])
                memories = [r.get("memory", "") for r in memories_list if r.get("memory")]
                if memories:
                    return memories
            except Exception as e:
                print(f"   ⚠️  Mem0 search failed, using local: {e}")
        
        # Fallback to local keyword search
        return self._local_recall(query, limit)
    
    def store_preference(self, key: str, value: Any):
        """Store user preference (e.g., preferred_restaurant: Oleana)"""
        # Store to Mem0 as a conversational memory
        if self.mem0_client:
            try:
                messages = [
                    {"role": "user", "content": f"My {key} is {value}"},
                    {"role": "assistant", "content": f"I'll remember that your {key} is {value}."}
                ]
                self.mem0_client.add(messages, user_id=self.user_id, metadata={"type": "preference", "key": key})
                print(f"   💾 Mem0: Stored preference → {key}: {value}")
            except Exception as e:
                print(f"   ⚠️  Mem0 preference store failed: {e}")
        
        # Always store locally
        self.local_memory.setdefault("preferences", {})[key] = value
        self._save_local()
        return True
    
    def get_preference(self, key: str) -> Optional[Any]:
        """Retrieve a specific preference"""
        prefs = self.local_memory.get("preferences", {})
        return prefs.get(key)
    
    def store_task_history(self, task_type: str, goal: str, outcome: str):
        """Log completed tasks for pattern learning"""
        if self.mem0_client:
            try:
                messages = [
                    {"role": "user", "content": f"Task completed: {task_type} - {goal}"},
                    {"role": "assistant", "content": f"Task '{task_type}' completed with outcome: {outcome}"}
                ]
                self.mem0_client.add(messages, user_id=self.user_id, metadata={"type": "task_history"})
            except Exception as e:
                print(f"   ⚠️  Mem0 task history store failed: {e}")
        
        # Local backup
        entry = {
            "type": "task_history",
            "task_type": task_type,
            "goal": goal,
            "outcome": outcome,
            "timestamp": datetime.now().isoformat()
        }
        self._local_store(entry)
        return True
    
    def get_all_memories(self) -> List[Dict]:
        """Retrieve all stored memories from Mem0 for this user"""
        if self.mem0_client:
            try:
                memories = self.mem0_client.get_all(filters={"user_id": self.user_id})
                # Mem0 may return different types
                if isinstance(memories, list):
                    return memories
                elif isinstance(memories, dict):
                    return memories.get("results", memories.get("memories", []))
                return []
            except Exception as e:
                print(f"   ⚠️  Mem0 get_all failed: {e}")
        return self.local_memory.get("entries", [])
    
    # ─── Local JSON Fallback ──────────────────────────────
    
    def _local_store(self, entry: Dict) -> bool:
        if entry["type"] == "preference":
            self.local_memory.setdefault("preferences", {})[entry["key"]] = entry["value"]
        else:
            self.local_memory.setdefault("entries", []).append(entry)
        
        self._save_local()
        return True
    
    def _local_recall(self, query: str, limit: int) -> List[str]:
        entries = self.local_memory.get("entries", [])
        # Simple keyword match (Mem0 provides semantic search when available)
        query_lower = query.lower()
        matches = [
            e["content"] for e in entries
            if query_lower in e.get("content", "").lower()
            or query_lower in e.get("category", "").lower()
        ]
        return matches[-limit:]
    
    def _load_local(self) -> Dict:
        if os.path.exists(self.local_file):
            with open(self.local_file, "r") as f:
                return json.load(f)
        return {"preferences": {}, "entries": []}
    
    def _save_local(self):
        with open(self.local_file, "w") as f:
            json.dump(self.local_memory, f, indent=2)
    
    def get_context_prompt(self) -> str:
        """Generate a memory context block for the system prompt"""
        lines = []
        
        # Preferences (from local cache — fast)
        prefs = self.local_memory.get("preferences", {})
        if prefs:
            lines.append("User Preferences:")
            for k, v in prefs.items():
                lines.append(f"  - {k}: {v}")
        
        # Recall relevant facts from Mem0 (semantic) or local (keyword)
        facts = self.recall_facts("user context preferences identity", limit=5)
        if facts:
            lines.append("Relevant Memories:")
            for f in facts:
                lines.append(f"  - {f}")
        
        return "\n".join(lines) if lines else ""
