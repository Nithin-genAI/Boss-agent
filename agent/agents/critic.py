# agents/critic.py — Validates execution results
from typing import Dict, Any


class CriticAgent:
    """
    Checks if execution succeeded and makes sense.
    If not, suggests retry or alternative.
    """
    
    def review(self, step_result: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        if not step_result.get("success"):
            return {
                "approved": False,
                "issue": step_result.get("error", "Unknown error"),
                "suggestion": "retry_once"
            }
        
        result = step_result.get("result", "")
        
        # Check for common failure signals
        failure_signals = ["not found", "error", "failed", "denied", "blocked", "timeout"]
        if any(sig in str(result).lower() for sig in failure_signals):
            return {
                "approved": False,
                "issue": f"Tool returned failure signal: {result[:100]}",
                "suggestion": "fallback_or_ask_user"
            }
        
        return {
            "approved": True,
            "summary": f"Step completed successfully. Output: {str(result)[:200]}"
        }
