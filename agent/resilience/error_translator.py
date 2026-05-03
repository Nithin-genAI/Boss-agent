# resilience/error_translator.py — User-friendly error messages
import re
from typing import Any


class ErrorTranslator:
    """
    Converts technical errors into actionable user messages.
    """
    
    PATTERNS = {
        r"permission denied": "I don't have permission to access that. You may need to grant access in System Settings → Privacy & Security.",
        r"file not found": "I couldn't find that file. Could you check the path or name?",
        r"directory not found": "That folder doesn't exist. Could you verify the location?",
        r"timeout": "The operation timed out. The service might be slow — want me to try again?",
        r"connection error": "I can't reach the internet right now. Check your connection and I'll retry.",
        r"blocked": "That action was blocked for safety. I can try a different approach.",
        r"no such file": "File not found. Want me to search for it?",
        r"operation not permitted": " macOS blocked that action. Grant permission in System Settings.",
        r"tool '.+' not found": "I don't have that capability configured. Let me try an alternative.",
        r"circuit open": "That service is temporarily unavailable. Using fallback instead.",
    }
    
    def translate(self, error_message: str, tool_name: str = "") -> str:
        """Convert technical error to user-friendly message."""
        error_lower = str(error_message).lower()
        
        for pattern, friendly in self.PATTERNS.items():
            if re.search(pattern, error_lower):
                if tool_name:
                    return f"[{tool_name}] {friendly}"
                return friendly
        
        # Generic fallback
        return f"I ran into an issue: {str(error_message)[:100]}. Let me try a different approach."
    
    def translate_success(self, tool_name: str, result: Any) -> str:
        """Format successful results nicely."""
        if isinstance(result, dict):
            if result.get("status") == "mock":
                return f"{tool_name} completed (demo mode). {result.get('message', '')}"
            if "confirmation_code" in result:
                return f"Done! Confirmation: {result['confirmation_code']}"
            if "order" in result:
                order = result["order"]
                return f"Order status: {order.get('status', 'unknown')}. ETA: {order.get('eta', 'N/A')}"
        
        if isinstance(result, str):
            if result.startswith("[MOCK]"):
                return result
            if len(result) > 200:
                return f"{tool_name} complete. Result: {result[:200]}..."
            return result
        
        return f"{tool_name} completed successfully."
