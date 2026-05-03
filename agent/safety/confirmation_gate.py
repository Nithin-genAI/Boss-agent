# safety/confirmation_gate.py — Smart confirmation system
from typing import Dict, Any, Optional
from safety.classifier import RiskLevel


class ConfirmationGate:
    """
    Asks for confirmation only when needed.
    Rules:
    - READ: Never confirm
    - WRITE: Confirm once per task, not per step
    - DESTRUCTIVE: Always confirm, with explicit warning
    """
    
    def __init__(self):
        self.task_confirmed: Dict[str, bool] = {}  # task_type -> confirmed
        self.pending_action: Optional[Dict] = None  # Action waiting for confirmation
    
    def should_confirm(self, tool_name: str, args: Dict[str, Any], task_type: str, classifier) -> tuple:
        """
        Returns: (needs_confirmation, message, risk_level)
        """
        risk = classifier.classify(tool_name, args)
        
        if risk == RiskLevel.READ:
            return False, "", risk
        
        if risk == RiskLevel.WRITE:
            # Check if this task type was already confirmed
            if task_type and self.task_confirmed.get(task_type):
                return False, "", risk
            return True, f"This will {self._describe_action(tool_name, args)}. Proceed?", risk
        
        if risk == RiskLevel.DESTRUCTIVE:
            return True, f"⚠️ DESTRUCTIVE: This will {self._describe_action(tool_name, args)}. This cannot be undone. Type YES to confirm:", risk
        
        return False, "", risk
    
    def confirm_task(self, task_type: str):
        """Mark a task type as confirmed for this session."""
        self.task_confirmed[task_type] = True
    
    def reset_task(self, task_type: str):
        """Clear confirmation for a task."""
        self.task_confirmed.pop(task_type, None)
    
    def reset_all(self):
        self.task_confirmed = {}
        self.pending_action = None
    
    def _describe_action(self, tool_name: str, args: Dict) -> str:
        """Human-readable description of what the tool will do."""
        descriptions = {
            "run_shell_command": f"run command: {args.get('command', 'unknown')}",
            "navigate_to_url": f"open website: {args.get('url', 'unknown')}",
            "type_on_page": f"type '{args.get('text', '')}' into {args.get('selector', 'field')}",
            "click_on_page": f"click on '{args.get('text', '')}'",
            "book_restaurant": "book a reservation",
        }
        return descriptions.get(tool_name, f"execute {tool_name}")
