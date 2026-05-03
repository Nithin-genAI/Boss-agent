# resilience/fallback.py — Fallback chains and mock data
from typing import Dict, Any, Callable


class FallbackChain:
    """
    If primary tool fails, try alternatives, then mock data.
    """
    
    MOCKS = {
        "book_restaurant": {
            "status": "success",
            "confirmation_code": "RES-MOCK-123",
            "message": "Table confirmed (mock mode — API unavailable)"
        },
        "check_order": {
            "status": "success",
            "order": {"id": "12345", "status": "shipped", "eta": "Tomorrow"}
        },
        "search_google": "Mock search results: 1. Example result A 2. Example result B 3. Example result C",
        "navigate_to_url": "Mock navigation: Page loaded successfully",
        "get_current_time": "2026-05-03 10:00:00",
    }
    
    def __init__(self):
        self.fallbacks: Dict[str, list] = {
            "read_file": ["find_file"],
            "navigate_to_url": ["search_google"],
            "search_google": ["navigate_to_url"],
        }
    
    def get_fallback(self, tool_name: str, original_args: Dict) -> tuple:
        """Return (fallback_tool_name, args) or None."""
        if tool_name in self.fallbacks:
            alts = self.fallbacks[tool_name]
            return alts[0], original_args
        return None, None
    
    def get_mock(self, tool_name: str, context: str = "") -> Any:
        """Return mock data for a tool."""
        if tool_name in self.MOCKS:
            mock = self.MOCKS[tool_name]
            if isinstance(mock, str):
                return f"[MOCK] {mock}"
            return mock
        
        # Context-aware mock generation
        if "restaurant" in context.lower():
            return self.MOCKS.get("book_restaurant", {"status": "mock", "message": "Mock response"})
        if "order" in context.lower():
            return self.MOCKS.get("check_order", {"status": "mock", "message": "Mock response"})
        
        return {"status": "mock", "message": f"Mock response for {tool_name}"}
