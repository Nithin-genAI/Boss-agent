# agents/orchestrator.py — The Conductor
from typing import Dict, Any, List
from agents.browser_agent import BrowserAgent
from agents.system_agent import SystemAgent
from agents.memory_agent import MemoryAgent
from agents.critic import CriticAgent
from agents.planner import PlannerAgent


class Orchestrator:
    """
    Receives user intent, delegates to specialist agents, aggregates results.
    """
    
    def __init__(self, registry, long_term_memory):
        self.browser = BrowserAgent(registry)
        self.system = SystemAgent(registry)
        self.memory = MemoryAgent(long_term_memory)
        self.critic = CriticAgent()
        self.planner = PlannerAgent()
    
    def route(self, intent: str, user_message: str, context: Dict[str, Any]) -> str:
        """Route to the right agent based on intent."""
        
        # Memory queries bypass everything
        if intent == "MEMORY_QUERY":
            result = self.memory.execute(user_message)
            return self._format_result(result)
        
        # Web actions → BrowserAgent
        if intent in ["WEB_ACTION", "NEW_TASK"] and any(k in user_message.lower() for k in 
            ["youtube", "google", "http", "search", "browse", "website", "open youtube", "play", "watch"]):
            result = self.browser.execute(user_message)
            critique = self.critic.review(result, "web")
            if not critique["approved"]:
                return f"Browser issue: {critique['issue']}. {critique.get('suggestion', '')}"
            return self._format_browser_result(result)
        
        # System actions → SystemAgent
        if any(k in user_message.lower() for k in 
            ["file", "folder", "directory", "open app", "screenshot", "run command", "find file", "read file"]):
            result = self.system.execute(user_message)
            return self._format_result(result)
        
        # Task-based flows → State machine (existing)
        if intent == "NEW_TASK":
            return "DELEGATE_TO_STATE_MACHINE"
        
        # Default
        return "DELEGATE_TO_LLM"
    
    def _format_browser_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"Browser failed: {result.get('error', 'Unknown error')}"
        
        action = result.get("action", "")
        
        if action == "youtube_search_play":
            query = result.get("query", "")
            clicked = result.get("clicked", False)
            steps = " → ".join(result.get("steps", []))
            snippet = result.get("page_snippet", "")[:400]
            
            status = "Video should be playing." if clicked else "Search results displayed. Click a video to play."
            return f"YouTube: {steps}. {status}\n\nPage preview:\n{snippet}"
        
        if action == "google_search":
            return f"Google results for '{result.get('query')}':\n\n{result.get('results', '')[:800]}"
        
        if action == "navigate":
            return f"Opened {result.get('url')}.\n\n{result.get('page_snippet', '')[:600]}"
        
        return f"Browser action complete: {action}"
    
    def _format_result(self, result: Dict[str, Any]) -> str:
        if not result.get("success"):
            return f"Error: {result.get('error', 'Failed')}"
            
        r_val = result.get('result', '')
        if isinstance(r_val, str) and (r_val.startswith('CONFIRM_REQUIRED:') or r_val.startswith('BLOCKED:')):
            return r_val
            
        action = result.get("action", "")
        if action == "recall":
            return result.get("fact", "Found it.")
        if action == "store":
            return f"Remembered: {result.get('stored', 'saved')}"
        if action == "read_file":
            return f"File contents:\n{result.get('content', '')[:1000]}"
        if action == "list_directory":
            return f"Files:\n{result.get('content', '')}"
        
        return f"Done: {action}"
