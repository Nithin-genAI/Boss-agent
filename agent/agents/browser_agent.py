# agents/browser_agent.py — Browser Specialist
import re
import time
from typing import Dict, Any


class BrowserAgent:
    def __init__(self, registry):
        self.registry = registry
    
    def execute(self, instruction: str) -> Dict[str, Any]:
        inst_lower = instruction.lower()
        
        # YouTube
        if "youtube" in inst_lower or "play" in inst_lower or "watch" in inst_lower:
            return self._youtube(instruction)
        
        # Google
        if "google" in inst_lower or "search" in inst_lower:
            return self._google(instruction)
        
        # Direct URL
        m = re.search(r'(https?://\S+)', instruction)
        if m:
            return self._navigate(m.group(1))
        
        # Generic site names (github.com, reddit.com, etc.)
        site_match = re.search(r'(?:go to|open|visit|navigate to|in (?:chrome|safari))\s+(\S+\.(?:com|org|io|net|dev))', inst_lower)
        if site_match:
            return self._navigate(f"https://{site_match.group(1)}")
        
        # Fallback: check for any domain-like pattern
        domain_match = re.search(r'(\w+\.(?:com|org|io|net|dev))', inst_lower)
        if domain_match:
            return self._navigate(f"https://{domain_match.group(1)}")
        
        return {"success": False, "error": "Unknown browser instruction"}
    
    def _youtube(self, instruction: str) -> Dict[str, Any]:
        query = "music"
        m = re.search(r'(?:search|for|play|watch)\s+(?:youtube\s+)?(?:for\s+)?["\']?(.+?)["\']?(?:\s+and\s+play|\s+on\s+youtube|\s*$)', instruction.lower())
        if m:
            query = m.group(1).strip()
            query = re.sub(r'^for\s+', '', query)
        
        import urllib.parse
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        self.registry.execute("navigate_to_url", {"url": search_url})
        time.sleep(5)
        
        clicked = False
        try:
            result = self.registry.execute("click_on_page", {"text": query})
            if "YT" in str(result) or "Clicked" in str(result):
                clicked = True
            time.sleep(3)
        except Exception as e:
            pass
            
        url = self.registry.execute("get_current_url", {})
        
        if "/watch" in str(url):
            snippet = f"Playing '{query}' on YouTube. Video loaded at: {url}"
        else:
            snippet = f"Searched YouTube for '{query}'. Results shown. Click a video to play."
            
        return {
            "success": True,
            "action": "youtube",
            "query": query,
            "clicked": clicked,
            "snippet": snippet
        }
    
    def _google(self, instruction: str) -> Dict[str, Any]:
        m = re.search(r'(?:search|for|look up)\s+(?:google\s+)?(?:for\s+)?(.+)', instruction.lower())
        query = m.group(1).strip() if m else "news"
        result = self.registry.execute("search_google", {"query": query})
        return {"success": True, "action": "google", "query": query, "results": result}
    
    def _navigate(self, url: str) -> Dict[str, Any]:
        result = self.registry.execute("navigate_to_url", {"url": url})
        time.sleep(1)
        page = self.registry.execute("read_page_text", {})
        return {
            "success": True,
            "action": "navigate",
            "url": url,
            "snippet": page[:600] if isinstance(page, str) else str(page)[:600]
        }
