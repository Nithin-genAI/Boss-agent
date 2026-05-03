# agents/planner.py — Breaks goals into executable steps
from typing import List, Dict, Any
from tasks.templates import TaskTemplate


class PlannerAgent:
    """
    Given a task template and collected fields, plans the execution steps.
    """
    
    def plan(self, template: TaskTemplate, collected: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate execution plan based on task type."""
        steps = []
        
        if template.name == "book_restaurant":
            steps = [
                {"agent": "executor", "action": "verify_restaurant", "params": collected},
                {"agent": "executor", "action": "check_availability", "params": collected},
                {"agent": "executor", "action": "hold_reservation", "params": collected},
            ]
        
        elif template.name == "check_order":
            steps = [
                {"agent": "executor", "action": "lookup_order", "params": collected},
            ]
        
        elif template.name == "open_and_summarize":
            steps = [
                {"agent": "executor", "action": "access_path", "params": collected},
                {"agent": "executor", "action": "read_content", "params": collected},
            ]
        
        elif template.name == "plan_trip":
            steps = [
                {"agent": "executor", "action": "search_hotels", "params": collected},
                {"agent": "executor", "action": "search_activities", "params": collected},
            ]
        
        else:
            steps = [
                {"agent": "executor", "action": "execute_task", "params": collected},
            ]
        
        return steps
