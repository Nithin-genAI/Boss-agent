# boss_kernel.py — Boss Agent Kernel (Production + Resilience + Safety)
import os
import re
import json
import time
from typing import List, Any, Dict
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage

from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODELS, BOSS_SYSTEM_PROMPT
from tools.registry import ToolRegistry
from memory.short_term import ShortTermMemory
from memory.working import WorkingMemory
from memory.long_term import LongTermMemory
from state_machine import TaskStateMachine
from intent_router import IntentRouter
from tasks.templates import TASK_REGISTRY
from agents.orchestrator import Orchestrator
from tools.resilient_registry import ResilientRegistry

from safety.classifier import ActionClassifier, RiskLevel
from safety.confirmation_gate import ConfirmationGate
from safety.undo_stack import UndoStack
from safety.policy import SafetyPolicy


class BossKernel:
    def __init__(self, model_key: str = "default", user_id: str = "default_user"):
        self.model_name = MODELS.get(model_key, MODELS["default"])
        self.user_id = user_id
        
        self.short_term = ShortTermMemory(max_turns=10)
        self.working = WorkingMemory()
        self.long_term = LongTermMemory(user_id=user_id)
        self.state_machine = TaskStateMachine()
        self.intent_router = IntentRouter()
        
        # Resilience layer (Phase 7)
        base_registry = ToolRegistry()
        self.registry = ResilientRegistry(base_registry)
        self.orchestrator = None
        
        # Safety layer (Phase 8)
        self.safety_classifier = ActionClassifier()
        self.confirmation_gate = ConfirmationGate()
        self.undo_stack = UndoStack()
        self.safety_policy = SafetyPolicy()
        # Pre-confirm web tools so browser doesn't prompt for every click
        self.confirmation_gate.confirm_task("web_agent")
        
        self.llm = ChatOpenAI(
            model=self.model_name,
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL,
            temperature=0.7,
            max_tokens=2000,
            model_kwargs={
                "extra_headers": {
                    "HTTP-Referer": "https://boss-agent.local",
                    "X-Title": "Boss Agent"
                }
            }
        )
        
        print(f"🧠 Boss Kernel initialized (Resilient Mode)")
        print(f"   Model: {self.model_name}")
        print(f"   User: {user_id}")

    def register_tools(self, tools: List[Any]):
        self.registry.register_many(tools)
        self.orchestrator = Orchestrator(self.registry, self.long_term)
        self.llm_with_tools = self.llm.bind_tools(self.registry.get_tools())
        print(f"   Tools loaded: {self.registry.list_tools()}")
        print(f"   Resilience: Retry=2, Circuit=3 failures, Mock={'ON' if self.registry.mock_mode else 'OFF'}")

    # ─── Main Think Loop ───────────────────────────────────

    def think(self, user_message: str, session_id: str = "default") -> str:
        msg_lower = user_message.lower().strip()
        
        context = {
            "current_state": self.state_machine.state,
            "current_task": self.state_machine.current_task,
        }
        
        intent = self.intent_router.classify(user_message, context)
        print(f"   🎯 Intent: {intent['intent']} (conf: {intent['confidence']})")
        
        # ─── 1. UNDO ───
        if intent["intent"] == "UNDO":
            return self.undo_stack.undo_last(self.registry)
        
        # ─── 2. CANCEL ───
        if intent["intent"] == "CANCEL":
            self.state_machine.cancel()
            return "Cancelled. What would you like to do?"
        
        # ─── 3. STATUS ───
        if intent["intent"] == "STATUS_CHECK":
            s = self.state_machine.get_summary()
            return f"Task: {s['task'] or 'None'} | State: {s['state']} | Have: {json.dumps(s['collected'])}"
        
        # ─── 4. MEMORY ───
        if intent["intent"] == "MEMORY_QUERY":
            return self._handle_memory_query(user_message)
        
        # ─── 5. SHELL ───
        if intent["intent"] == "SHELL_COMMAND":
            return self._handle_shell(user_message)
        
        # ─── 6. WEB ───
        if intent["intent"] == "WEB_ACTION":
            return self._handle_web(user_message)
        
        # ─── 7. TASK FLOW ───
        if intent["intent"] == "NEW_TASK":
            return self._handle_new_task(user_message, intent)
        
        if intent["intent"] == "INFO_PROVISION" and self.state_machine.is_mid_task():
            return self._handle_info_provision(user_message)
        
        if intent["intent"] == "CORRECTION" and self.state_machine.is_mid_task():
            return self._handle_correction(intent)
        
        if intent["intent"] == "CONFIRM" and self.state_machine.state == "confirming":
            self.state_machine.confirm(True)
            return "Executing your request..."
        
        if intent["intent"] == "DECLINE" and self.state_machine.state == "confirming":
            self.state_machine.confirm(False)
            return "What would you like to change?"
        
        # ─── 8. CLARIFICATION (mid-task question/garbage) ───
        if intent["intent"] == "CLARIFICATION" and self.state_machine.is_mid_task():
            return f"I need a valid answer. {self.state_machine.get_next_question()}"
        
        # ─── 9. GENERAL CHAT ───
        return self._general_chat(user_message)
    
    # ─── Handler Methods ───────────────────────────────────
    
    def _handle_memory_query(self, message: str) -> str:
        name = self.long_term.get_preference("user_name")
        if name:
            return f"Your name is {name}."
        return "I don't know your name yet. Tell me and I'll remember it."
    
    def _handle_shell(self, message: str) -> str:
        cmd = message
        for prefix in ["run command", "execute command", "run shell", "shell command"]:
            cmd = cmd.replace(prefix, "", 1)
        cmd = cmd.strip()
        
        # Safety policy check (Phase 8)
        allowed, reason = self.safety_policy.check("run_shell_command", {"command": cmd})
        if not allowed:
            return f"BLOCKED: {reason}"
        
        # Hard block the worst commands
        blocked = ["rm -rf /", "rm -rf ~", "rm -rf /*", "sudo rm", "mkfs", "dd if=", ":(){:|:&};:"]
        if any(b in cmd for b in blocked):
            return "BLOCKED: That command is permanently forbidden for safety."
        
        result = self.registry.execute("run_shell_command", {"command": cmd})
        self.undo_stack.push("run_shell_command", {"command": cmd}, result, self.registry)
        return self._format_response(str(result))
    
    def _handle_web(self, message: str) -> str:
        """Route web requests through BrowserAgent."""
        if self.orchestrator:
            result = self.orchestrator.browser.execute(message)
            if result.get("success"):
                action = result.get("action", "")
                snippet = result.get("snippet", result.get("results", ""))
                snippet = self._clean_snippet(snippet)
                
                if action == "youtube":
                    return snippet or "YouTube action complete."
                if action == "google":
                    return snippet or "Google search complete."
                if action == "navigate":
                    url = result.get('url', '')
                    if snippet:
                        return f"Opened {url}.\n\n{snippet}"
                    return f"Opened {url} in Safari."
                return snippet or "Done."
            return f"Browser error: {result.get('error', 'Unknown')}"
        return "Browser not available."
    
    def _clean_snippet(self, snippet) -> str:
        """Remove error messages from browser output."""
        if not snippet:
            return ""
        text = str(snippet)[:600]
        # Strip AppleScript/Safari error noise
        if "Error:" in text or "execution error" in text:
            # Try to salvage any real content before the error
            lines = [l for l in text.split('\n') if l.strip()
                     and "Error:" not in l
                     and "execution error" not in l
                     and "Let me try" not in l
                     and "ran into an issue" not in l]
            return '\n'.join(lines).strip()
        return text
    
    def _handle_new_task(self, message: str, intent: Dict) -> str:
        if self.state_machine.is_mid_task():
            self.state_machine.cancel()
        
        task_type = intent.get("task_type", "unknown")
        if task_type in TASK_REGISTRY:
            self.state_machine.start_task(task_type)
            self._prefill_from_memory()
            return self._format_response(f"I'll help you with that. {self.state_machine.get_next_question()}")
        
        return "I can help with: booking tables, checking orders, planning trips, opening files, or browsing the web."
    
    def _handle_info_provision(self, message: str) -> str:
        extracted = self._extract_fields(message)
        
        if not extracted:
            return f"I need a valid answer. {self.state_machine.get_next_question()}"
        
        result = {}
        for field, value in extracted.items():
            result = self.state_machine.update_field(field, value)
        
        if result.get("status") == "confirming":
            return f"Ready: {json.dumps(self.state_machine.collected)}. Shall I proceed?"
        
        return self._format_response(result.get("next_question", "What else?"))
    
    def _handle_correction(self, intent: Dict) -> str:
        value = intent.get("value", "")
        missing = self.state_machine.template.get_missing(self.state_machine.collected) if self.state_machine.template else []
        
        field = None
        if re.search(r'\d{1,2}(?::\d{2})?\s*(?:am|pm)', value):
            field = "time"
        elif any(d in value for d in ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "tomorrow", "today"]):
            field = "date"
        elif value.isdigit():
            field = "people"
        elif missing:
            field = missing[0]
        
        if field:
            self.state_machine.collected[field] = value
            return f"Updated {field} to '{value}'. {self.state_machine.get_next_question()}"
        
        return "Which field should I update?"
    
    # ─── Field Extraction ──────────────────────────────────
    
    def _extract_fields(self, text: str) -> Dict[str, Any]:
        """Extract ONLY the next needed field with strict validation."""
        extracted = {}
        text_stripped = text.strip()
        text_lower = text_stripped.lower()
        
        if not self.state_machine.template:
            return {}
        
        missing = self.state_machine.template.get_missing(self.state_machine.collected)
        if not missing:
            return {}
        
        next_field = missing[0]
        
        # ─── REJECT GARBAGE ───
        reject_patterns = [
            r'^(why|how|what|when|where|who|which)\s',
            r'^(can|could|would|will|did|is|are|do)\s',
            r'^(run|execute|sudo|rm|cat|ls|mkdir)\s',
            r'^(hey|hi|hello|yo|sup|ok|okay|thanks|bye)\b',
        ]
        for pattern in reject_patterns:
            if re.search(pattern, text_lower):
                return {}
        
        # ─── FIELD-SPECIFIC EXTRACTION ───
        
        if next_field == "time":
            m = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)', text_lower)
            if m:
                extracted["time"] = m.group(1)
            return extracted
        
        if next_field == "people":
            if text_stripped.isdigit() and int(text_stripped) < 50:
                extracted["people"] = int(text_stripped)
            elif text_lower in ["just me", "alone", "myself", "one"]:
                extracted["people"] = 1
            elif text_lower == "two":
                extracted["people"] = 2
            return extracted
        
        if next_field == "restaurant":
            clean = text_stripped.strip(".,!?;:")
            if len(clean) > 1 and len(clean) < 50:
                extracted["restaurant"] = clean.title() if clean[0].islower() else clean
            return extracted
        
        if next_field == "date":
            days = ["monday", "tuesday", "wednesday", "thursday", "friday",
                    "saturday", "sunday", "tomorrow", "today"]
            if any(d in text_lower for d in days) or re.search(r'\d{1,2}[/-]\d{1,2}', text_stripped):
                extracted["date"] = text_stripped
            return extracted
        
        if next_field == "target_path":
            if "/" in text_stripped or "~" in text_stripped:
                extracted["target_path"] = text_stripped
            return extracted
        
        if next_field == "order_id":
            m = re.search(r'#?(\d{5,})', text_stripped)
            if m:
                extracted["order_id"] = m.group(1)
            return extracted
        
        # Generic fallback
        if 0 < len(text_stripped) < 100:
            extracted[next_field] = text_stripped
        
        return extracted
    
    # ─── Support Methods ───────────────────────────────────
    
    def _prefill_from_memory(self):
        if self.state_machine.current_task == "book_restaurant":
            name = self.long_term.get_preference("user_name")
            if name:
                self.state_machine.collected["name"] = name
    
    def _general_chat(self, user_message: str) -> str:
        self.short_term.add(HumanMessage(content=user_message))
        system_msg = SystemMessage(content=self._build_system_prompt())
        
        while True:
            messages = [system_msg] + self.short_term.get()
            response = self.llm_with_tools.invoke(messages)
            self.short_term.add(response)
            
            if not response.tool_calls:
                break
                
            for tc in response.tool_calls:
                result = self.registry.execute(tc["name"], tc["args"])
                self.short_term.add(ToolMessage(content=str(result), tool_call_id=tc["id"]))
        
        self._learn(user_message, response.content)
        return response.content if response.content else "Done."
    
    def _build_system_prompt(self) -> str:
        base = BOSS_SYSTEM_PROMPT
        
        if self.state_machine.is_mid_task():
            s = self.state_machine.get_summary()
            base += f"\n\nTASK: {s['task']} | STATE: {s['state']} | HAVE: {json.dumps(s['collected'])}"
        
        name = self.long_term.get_preference("user_name")
        if name:
            base += f"\n\nUSER NAME: {name}"
        
        return base
    
    def _learn(self, user_msg: str, assistant_msg: str):
        m = re.search(r"(?:my name is|i am|call me)\s+([A-Z][a-zA-Z]+)", user_msg)
        if m:
            self.long_term.store_preference("user_name", m.group(1))
            print(f"   💾 Mem0: Stored name '{m.group(1)}'")
    
    def _format_response(self, text: str) -> str:
        if not text:
            return "Done."
        text = str(text)
        text = re.sub(r'#{1,6}\s*', '', text)
        text = re.sub(r'\*\*', '', text)
        text = re.sub(r'\*', '', text)
        text = re.sub(r'`', '', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()
    
    def reset_memory(self):
        self.short_term.clear()
        self.state_machine.reset()
        print("🔄 Reset complete")

    def get_status(self) -> dict:
        return {
            "model": self.model_name,
            "user": self.user_id,
            "tools": self.registry.list_tools(),
            "state": self.state_machine.get_summary(),
        }