# intent_router.py — Bulletproof Intent Router for Boss
import re
from typing import Dict, Any


class IntentRouter:
    """
    Zero-tolerance classification. Every input goes to exactly one handler.
    """
    
    # ─── Pattern Lists ─────────────────────────────────────
    
    CANCEL_WORDS = ["cancel", "stop it", "never mind", "forget it", "abort", "end this", "cancel it", "stop this", "escape", "reset task", "exit task"]
    UNDO_WORDS = ["undo", "take back", "reverse that", "go back"]
    STATUS_WORDS = ["status", "what were we doing", "where are we", "what's the status", "what was i doing"]
    
    SHELL_PREFIXES = ["run command", "execute command", "run shell", "shell command",
                      "rm ", "sudo ", "cat ", "ls ", "mkdir ", "touch ", "python ", "pip ",
                      "cd ", "pwd", "echo ", "grep ", "find ", "chmod ", "chown "]
    
    WEB_TRIGGERS = [
        "youtube", "google", "github", "http", "open youtube",
        "search youtube", "go to", "navigate", "browse",
        "in chrome", "in browser", "in safari", "open website", "visit",
        "play video", "watch", "new tab", "switch tab", "screenshot page",
        ".com", ".org", ".net", ".in", ".io"
    ]
    
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
        # Must use multi-word phrases to avoid catching "book train", "book ticket", etc.
        "book_restaurant": ["book a table", "book a restaurant", "book restaurant", "reserve a table",
                            "reservation at", "dinner reservation", "lunch reservation"],
        "check_order": ["check order", "track order", "order status", "where is my order", "package tracking"],
        "plan_trip": ["plan trip", "plan a trip", "vacation", "book a hotel"],
        "file_complaint": ["file a complaint", "support ticket", "complaint about"],
        "open_and_summarize": ["open folder", "summarize directory", "show me files", "list files in"],
    }

    # These patterns BLOCK new task detection — they belong to GENERAL_CHAT
    TASK_BLOCK_PATTERNS = [
        "book train", "book ticket", "train ticket", "irctc", "book flight",
        "open ", "search for", "find ", "go to", "navigate to"
    ]
    
    # ─── Main Classify Method ──────────────────────────────
    
    def classify(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        context = context or {}
        msg_lower = message.lower().strip()
        current_task = context.get("current_task")
        current_state = context.get("current_state", "idle")
        
        # ─── 0. EMPTY / GARBAGE ───
        if not msg_lower or len(msg_lower) < 1:
            return {"intent": "GENERAL_CHAT", "confidence": 1.0, "raw": message}
        
        # ─── 1. CANCEL / UNDO / STATUS (ALWAYS first — must be able to escape any task) ───
        if any(msg_lower == w or w in msg_lower for w in self.CANCEL_WORDS):
            return {"intent": "CANCEL", "confidence": 1.0, "raw": message}
        
        if any(msg_lower == w or msg_lower.startswith(w) for w in self.UNDO_WORDS):
            return {"intent": "UNDO", "confidence": 1.0, "raw": message}
        
        if any(msg_lower == w or msg_lower.startswith(w) for w in self.STATUS_WORDS):
            return {"intent": "STATUS_CHECK", "confidence": 1.0, "raw": message}
        
        # ─── 2. SHELL COMMANDS (highest priority — dangerous) ───
        for prefix in self.SHELL_PREFIXES:
            if msg_lower.startswith(prefix):
                return {"intent": "SHELL_COMMAND", "confidence": 0.98, "raw": message}
        
        # ─── 2.5 COMPLEX ANALYSIS (requires LLM) ───
        complex_triggers = ["screenshot", "summarize", "analyze", "analyse", "what is there", "what is on", "tell me what", "photo", "picture", "youtube", "chrome", "subscriptions", "gmail",
                            "github", "repo", "repository", "create repo", "update repo", "create issue", "read readme", "list repos", "list issues", "comment on", "close issue", "push to", "commit"]
        if any(c in msg_lower for c in complex_triggers):
            return {"intent": "GENERAL_CHAT", "confidence": 0.96, "raw": message}
            
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
        # First check if this is blocked (e.g., "book train" should NOT trigger book_restaurant)
        is_blocked = any(b in msg_lower for b in self.TASK_BLOCK_PATTERNS)
        if not is_blocked:
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