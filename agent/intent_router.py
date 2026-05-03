# intent_router.py — Bulletproof Intent Router for Boss
import re
from typing import Dict, Any


class IntentRouter:
    """
    Zero-tolerance classification. Every input goes to exactly one handler.
    """
    
    # ─── Pattern Lists ─────────────────────────────────────
    
    CANCEL_WORDS = ["cancel", "stop", "never mind", "forget it", "abort", "end this", "quit"]
    UNDO_WORDS = ["undo", "take back", "reverse that", "go back"]
    STATUS_WORDS = ["status", "what were we doing", "where are we", "what's the status", "what was i doing"]
    
    SHELL_PREFIXES = ["run command", "execute command", "run shell", "shell command",
                      "rm ", "sudo ", "cat ", "ls ", "mkdir ", "touch ", "python ", "pip ",
                      "cd ", "pwd", "echo ", "grep ", "find ", "chmod ", "chown "]
    
    WEB_TRIGGERS = ["youtube", "google.com", "github.com", "http://", "https://",
                    "open youtube", "search youtube", "go to ", "navigate to ", "browse ",
                    "in chrome", "in safari", "open website", "visit ", "play video",
                    "watch ", "search google", "look up "]
    
    CHAT_GREETINGS = ["hey", "hi", "hello", "yo", "sup", "hola", "howdy", "greetings",
                      "ok", "okay", "sure", "thanks", "thank you", "bye", "goodbye"]
    
    QUESTION_STARTERS = ["why", "how", "what", "when", "where", "who", "which",
                         "can you", "could you", "would you", "will you", "did you",
                         "is it", "are you", "do you"]
    
    CONFIRM_WORDS = ["yes", "yeah", "yep", "sure", "ok", "okay", "proceed", "go ahead",
                     "confirm", "do it", "yes please", "absolutely", "definitely"]
    
    DECLINE_WORDS = ["no", "nope", "nah", "not really", "change", "different", "wrong",
                     "not quite", "no thanks", "don't"]
    
    CORRECTION_STARTERS = ["actually", "wait", "no i meant", "change it to", "make it",
                           "instead", "not ", "i meant", "let's make it", "correction:"]
    
    TASK_PATTERNS = {
        "book_restaurant": ["book", "table", "restaurant", "reserve", "reservation", "dinner at", "lunch at"],
        "check_order": ["check order", "track order", "order status", "where is my order", "package tracking"],
        "plan_trip": ["plan trip", "plan a trip", "travel to", "vacation", "hotel", "flight", "book a hotel"],
        "file_complaint": ["complaint", "support ticket", "file a complaint", "issue with", "problem with"],
        "open_and_summarize": ["open folder", "read file", "summarize directory", "show me files", "list files in"],
    }
    
    # ─── Main Classify Method ──────────────────────────────
    
    def classify(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        context = context or {}
        msg_lower = message.lower().strip()
        current_task = context.get("current_task")
        current_state = context.get("current_state", "idle")
        
        # ─── 0. EMPTY / GARBAGE ───
        if not msg_lower or len(msg_lower) < 1:
            return {"intent": "GENERAL_CHAT", "confidence": 1.0, "raw": message}
        
        # ─── 1. EXACT MATCH SHORTCUTS (fast path) ───
        if msg_lower in self.CANCEL_WORDS:
            return {"intent": "CANCEL", "confidence": 1.0, "raw": message}
        
        if msg_lower in self.UNDO_WORDS:
            return {"intent": "UNDO", "confidence": 1.0, "raw": message}
        
        if any(msg_lower == w or msg_lower.startswith(w + " ") for w in self.STATUS_WORDS):
            return {"intent": "STATUS_CHECK", "confidence": 1.0, "raw": message}
        
        # ─── 2. SHELL COMMANDS (highest priority — dangerous) ───
        for prefix in self.SHELL_PREFIXES:
            if msg_lower.startswith(prefix):
                return {"intent": "SHELL_COMMAND", "confidence": 0.98, "raw": message}
        
        # ─── 3. WEB ACTIONS ───
        for trigger in self.WEB_TRIGGERS:
            if trigger in msg_lower:
                return {"intent": "WEB_ACTION", "confidence": 0.95, "raw": message}
        
        # ─── 4. CHAT / GREETINGS (block before task flow) ───
        if msg_lower in self.CHAT_GREETINGS or any(msg_lower.startswith(g + " ") for g in self.CHAT_GREETINGS):
            return {"intent": "GENERAL_CHAT", "confidence": 0.9, "raw": message}
        
        # ─── 5. QUESTIONS (block before task flow if not mid-task) ───
        if any(msg_lower.startswith(q) for q in self.QUESTION_STARTERS):
            if not current_task:
                return {"intent": "GENERAL_CHAT", "confidence": 0.85, "raw": message}
            return {"intent": "CLARIFICATION", "confidence": 0.8, "raw": message}
        
        # ─── 6. MEMORY QUERIES ───
        memory_patterns = [r"what('?s| is) my name", r"who am i", r"what do i like",
                          r"what do i prefer", r"remind me", r"what did (we|i) (say|do)",
                          r"what was my", r"do you know my", r"tell me about myself"]
        for pattern in memory_patterns:
            if re.search(pattern, msg_lower):
                return {"intent": "MEMORY_QUERY", "confidence": 0.95, "raw": message}
        
        # ─── 7. MID-TASK FLOW ───
        if current_task and current_state in ["collecting", "confirming", "revising"]:
            
            # Confirmations
            if msg_lower in self.CONFIRM_WORDS or any(msg_lower.startswith(c) for c in self.CONFIRM_WORDS):
                return {"intent": "CONFIRM", "confidence": 0.95, "raw": message}
            
            # Declines
            if msg_lower in self.DECLINE_WORDS or any(msg_lower.startswith(d) for d in self.DECLINE_WORDS):
                return {"intent": "DECLINE", "confidence": 0.9, "raw": message}
            
            # Corrections
            for starter in self.CORRECTION_STARTERS:
                if msg_lower.startswith(starter):
                    clean = msg_lower
                    for s in self.CORRECTION_STARTERS:
                        clean = clean.replace(s, "", 1).strip()
                    return {"intent": "CORRECTION", "confidence": 0.9, "value": clean, "raw": message}
            
            # Info provision — STRICT validation
            if self._is_valid_input(msg_lower, current_task):
                return {"intent": "INFO_PROVISION", "confidence": 0.85, "raw": message}
            else:
                return {"intent": "CLARIFICATION", "confidence": 0.7, "raw": message}
        
        # ─── 8. NEW TASKS ───
        for task_type, keywords in self.TASK_PATTERNS.items():
            if any(k in msg_lower for k in keywords):
                return {"intent": "NEW_TASK", "confidence": 0.85, "task_type": task_type, "raw": message}
        
        # ─── 9. FALLBACK ───
        return {"intent": "GENERAL_CHAT", "confidence": 0.6, "raw": message}
    
    # ─── Helper Methods ────────────────────────────────────
    
    def _is_valid_input(self, msg_lower: str, current_task: str) -> bool:
        """Check if input is valid for the current task field."""
        if any(msg_lower.startswith(p) for p in self.SHELL_PREFIXES):
            return False
        if any(msg_lower.startswith(q) for q in self.QUESTION_STARTERS):
            return False
        if msg_lower in self.CHAT_GREETINGS:
            return False
        if len(msg_lower) < 1:
            return False
        return True
    
    def extract_task_type(self, message: str) -> str:
        msg_lower = message.lower()
        for task_type, keywords in self.TASK_PATTERNS.items():
            if any(k in msg_lower for k in keywords):
                return task_type
        return "unknown"