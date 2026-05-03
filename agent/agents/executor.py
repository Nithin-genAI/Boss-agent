# agents/executor.py — Runs tools and reports results
from typing import Dict, Any
from tools.registry import ToolRegistry


class ExecutorAgent:
    """
    Executes the actual tools. Bridges between state machine and tool registry.
    """
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
    
    def execute_step(self, step: Dict[str, Any]) -> Dict[str, Any]:
        action = step.get("action")
        params = step.get("params", {})
        
        # Map task actions to actual tools
        action_to_tool = {
            "verify_restaurant": "get_current_time",  # Mock
            "check_availability": "get_current_time",  # Mock
            "hold_reservation": "get_current_time",  # Mock
            "lookup_order": "get_current_time",  # Mock
            "access_path": "list_directory",
            "read_content": "read_file",
            "search_hotels": "get_current_time",
            "execute_task": "get_current_time",
        }
        
        tool_name = action_to_tool.get(action)
        
        if not tool_name:
            return {"success": False, "error": f"No tool mapped for action: {action}"}
        
        try:
            result = self.registry.execute(tool_name, params)
            return {"success": True, "action": action, "result": result}
        except Exception as e:
            return {"success": False, "action": action, "error": str(e)}
