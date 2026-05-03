# memory/working.py — Active Task State
from typing import Dict, Any, Optional
from datetime import datetime


class WorkingMemory:
    def __init__(self):
        self.active_task: Optional[str] = None      # e.g., "book_restaurant"
        self.task_goal: str = ""                    # e.g., "Book a table at Oleana"
        self.step: int = 0                          # Current step number
        self.collected: Dict[str, Any] = {}         # Facts gathered so far
        self.missing: list = []                     # Fields still needed
        self.status: str = "idle"                   # idle | collecting | awaiting_confirmation | executing | completed | failed
        self.last_action: Optional[str] = None      # What we just did
        self.correction_pending: bool = False       # Did user just correct us?
        self.created_at: str = datetime.now().isoformat()
    
    def start_task(self, task_type: str, goal: str, required_fields: list):
        self.active_task = task_type
        self.task_goal = goal
        self.step = 0
        self.collected = {}
        self.missing = required_fields.copy()
        self.status = "collecting"
        self.correction_pending = False
        self.created_at = datetime.now().isoformat()
        print(f"   📝 Working memory: Started task '{task_type}' — need: {required_fields}")
    
    def update_field(self, field: str, value: Any):
        self.collected[field] = value
        if field in self.missing:
            self.missing.remove(field)
        
        if not self.missing:
            self.status = "awaiting_confirmation"
        else:
            self.status = "collecting"
    
    def next_step(self):
        self.step += 1
    
    def mark_executing(self):
        self.status = "executing"
    
    def mark_completed(self):
        self.status = "completed"
        print(f"   ✅ Working memory: Task '{self.active_task}' completed")
    
    def mark_failed(self, reason: str):
        self.status = "failed"
        print(f"   ❌ Working memory: Task failed — {reason}")
    
    def apply_correction(self, field: str, new_value: Any):
        """User corrected a field — update without restarting"""
        self.collected[field] = new_value
        self.correction_pending = True
        self.status = "collecting" if self.missing else "awaiting_confirmation"
        print(f"   🔄 Working memory: Corrected '{field}' → {new_value}")
    
    def cancel_task(self):
        print(f"   🛑 Working memory: Task '{self.active_task}' cancelled")
        self.__init__()  # Reset
    
    def get_summary(self) -> dict:
        return {
            "task": self.active_task,
            "goal": self.task_goal,
            "step": self.step,
            "collected": self.collected,
            "missing": self.missing,
            "status": self.status,
            "correction_pending": self.correction_pending
        }
    
    def is_mid_task(self) -> bool:
        return self.active_task is not None and self.status not in ["completed", "failed", "idle"]
