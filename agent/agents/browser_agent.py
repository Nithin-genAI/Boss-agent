# agents/browser_agent.py — Selenium Chrome BrowserAgent
import re
import time
from typing import Dict, Any


class BrowserAgent:
    def __init__(self, registry):
        self.registry = registry
    
    def execute(self, instruction: str) -> Dict[str, Any]:
        inst_lower = instruction.lower()
        
        if "youtube" in inst_lower or "play" in inst_lower or "watch" in inst_lower:
            return self._youtube(instruction)
        
        if "google" in inst_lower or "search" in inst_lower:
            return self._google(instruction)
        
        m = re.search(r'(https?://\S+)', instruction)
        if m:
            return self._navigate(m.group(1))
        
        if "open" in inst_lower:
            return self._navigate("https://google.com")
        
        if "click" in inst_lower:
            text = instruction.replace("click", "").strip()
            return self._click(text)
        
        if "read" in inst_lower:
            return self._read()
        
        return {"success": False, "error": "Unknown instruction"}
    
    def _youtube(self, instruction: str) -> Dict[str, Any]:
        query = "music"
        m = re.search(r'(?:for|search|play|watch)\s+["\']?(.+?)["\']?(?:\s+and\s+play|\s+on\s+youtube|\s*$)', instruction.lower())
        if m:
            query = m.group(1).strip()
        
        self.registry.execute("browser_go", {"url": "https://www.youtube.com"})
        time.sleep(3)
        self.registry.execute("browser_type", {"selector": "search_query", "text": query})
        time.sleep(0.5)
        self.registry.execute("browser_press", {"key": "Enter"})
        time.sleep(4)
        
        # Click first video
        clicked = False
        try:
            self.registry.execute("browser_click", {"text": query.title()})
            clicked = True
        except:
            pass
        
        page = self.registry.execute("browser_read", {})
        url = self.registry.execute("browser_get_url", {})
        
        return {
            "success": True,
            "action": "youtube",
            "query": query,
            "clicked": clicked,
            "url": url,
            "snippet": str(page)[:500]
        }
    
    def _google(self, instruction: str) -> Dict[str, Any]:
        m = re.search(r'(?:search|for|look up)\s+(?:google\s+)?(?:for\s+)?(.+)', instruction.lower())
        query = m.group(1).strip() if m else "news"
        result = self.registry.execute("browser_search", {"query": query, "engine": "google"})
        return {"success": True, "action": "google", "query": query, "results": result}
    
    def _navigate(self, url: str) -> Dict[str, Any]:
        result = self.registry.execute("browser_go", {"url": url})
        time.sleep(2)
        page = self.registry.execute("browser_read", {})
        return {"success": True, "action": "navigate", "url": url, "snippet": str(page)[:500]}
    
    def _click(self, text: str) -> Dict[str, Any]:
        result = self.registry.execute("browser_click", {"text": text})
        time.sleep(2)
        return {"success": True, "action": "click", "target": text}
    
    def _read(self) -> Dict[str, Any]:
        page = self.registry.execute("browser_read", {})
        return {"success": True, "action": "read", "content": str(page)[:1000]}
