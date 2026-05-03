# state_machine.py — Fixed Task State Machine for Boss
from typing import Dict, Any, Optional
from datetime import datetime
from tasks.templates import TaskTemplate, TASK_REGISTRY


class TaskStateMachine:
    STATES = ["idle", "collecting", "confirming", "revising", "executing", "completed", "failed", "cancelled"]
    
    def __init__(self):
        self.state: str = "idle"
        self.current_task: Optional[str] = None
        self.template: Optional[TaskTemplate] = None
        self.collected: Dict[str, Any] = {}
        self.step_index: int = 0
        self.history: list = []
        self.last_error: Optional[str] = None
        self.correction_target: Optional[str] = None
        self.task_goal: str = ""
    
    def start_task(self, task_name: str) -> bool:
        if task_name not in TASK_REGISTRY:
            return False
        
        self.current_task = task_name
        self.template = TASK_REGISTRY[task_name]
        self.task_goal = self.template.description
        self.collected = {}
        self.step_index = 0
        self.state = "collecting"
        self.last_error = None
        self.correction_target = None
        self._log("started", f"Task {task_name}")
        return True
    
    def update_field(self, field: str, value: Any) -> Dict[str, Any]:
        self.collected[field] = value
        self.correction_target = None
        
        if self.template:
            missing = self.template.get_missing(self.collected)
            if not missing:
                if self.template.confirmation_required:
                    self.state = "confirming"
                else:
                    self.state = "executing"
            else:
                self.state = "collecting"
            
            return {
                "status": self.state,
                "missing": missing,
                "collected": self.collected,
                "next_question": self.get_next_question()
            }
        
        return {"status": "error", "message": "No template"}
    
    def apply_correction(self, field: str, new_value: Any) -> Dict[str, Any]:
        old = self.collected.get(field, "N/A")
        self.collected[field] = new_value
        self.correction_target = field
        self.state = "collecting"
        
        missing = self.template.get_missing(self.collected) if self.template else []
        self._log("corrected", f"{field}: {old} -> {new_value}")
        
        return {
            "status": "corrected",
            "field": field,
            "old": old,
            "new": new_value,
            "missing": missing,
            "next_question": self.get_next_question()
        }
    
    def confirm(self, confirmed: bool = True) -> str:
        if confirmed:
            self.state = "executing"
            self._log("confirmed", "Proceeding")
            return "executing"
        else:
            self.state = "revising"  # KEY FIX: was "cancelled"
            self._log("revising", "User wants changes")
            return "revising"
    
    def mark_step_complete(self, step_result: Any = None):
        self.step_index += 1
        if self.template and self.step_index >= len(self.template.steps):
            self.state = "completed"
            self._log("completed", str(step_result)[:100])
        else:
            self._log("step", f"Step {self.step_index}")
    
    def mark_failed(self, reason: str):
        self.state = "failed"
        self.last_error = reason
        self._log("failed", reason)
    
    def cancel(self):
        self.state = "cancelled"
        self._log("cancelled", "By user")
    
    def reset(self):
        self.__init__()
    
    def is_mid_task(self) -> bool:
        return self.active_task is not None and self.state in ["collecting", "confirming", "revising", "executing"]
    
    @property
    def active_task(self) -> Optional[str]:
        return self.current_task if self.state not in ["idle", "completed", "failed", "cancelled"] else None
    
    def get_next_question(self) -> str:
        if self.state == "revising":
            return "What would you like to change? Tell me the field and new value."
        
        if self.state == "confirming":
            import json
            return f"Here's what I have: {json.dumps(self.collected)}. Shall I proceed?"
        
        if self.template:
            missing = self.template.get_missing(self.collected)
            return self._generate_next_question(missing)
        
        return "What do you need?"
    
    def get_summary(self) -> Dict[str, Any]:
        return {
            "task": self.current_task,
            "goal": self.task_goal,
            "state": self.state,
            "step": self.step_index,
            "collected": self.collected,
            "missing": self.template.get_missing(self.collected) if self.template else [],
            "confirmation_needed": self.state == "confirming",
            "last_error": self.last_error,
        }
    
    def _generate_next_question(self, missing: list) -> str:
        if not missing:
            return "All set!"
        
        field = missing[0]
        questions = {
            "restaurant": "Which restaurant?",
            "time": "What time?",
            "people": "How many people?",
            "date": "Which date?",
            "destination": "Where to?",
            "dates": "What dates?",
            "travelers": "How many travelers?",
            "order_id": "What's the order ID?",
            "issue_type": "What type of issue?",
            "description": "Please describe the problem.",
            "target_path": "Which file or folder should I open?",
        }
        return questions.get(field, f"What's the {field}?")
    
    def _log(self, event: str, detail: str):
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "detail": detail
        })