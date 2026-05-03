# memory/short_term.py — Conversation Buffer
from typing import List, Any
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage


class ShortTermMemory:
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns  # 10 turns = 20 messages (user + assistant)
        self.messages: List[Any] = []
    
    def add(self, message: Any):
        self.messages.append(message)
        self._trim()
    
    def add_many(self, messages: List[Any]):
        for m in messages:
            self.messages.append(m)
        self._trim()
    
    def get(self) -> List[Any]:
        return self.messages.copy()
    
    def clear(self):
        self.messages = []
    
    def _trim(self):
        # Keep system message + last N turns
        system_msgs = [m for m in self.messages if isinstance(m, SystemMessage)]
        other_msgs = [m for m in self.messages if not isinstance(m, SystemMessage)]
        
        # Keep last max_turns * 2 messages (user + assistant per turn)
        kept = other_msgs[-(self.max_turns * 2):]
        self.messages = system_msgs + kept
    
    def last_user_message(self) -> str:
        for m in reversed(self.messages):
            if isinstance(m, HumanMessage):
                return m.content
        return ""
    
    def turn_count(self) -> int:
        return len([m for m in self.messages if isinstance(m, HumanMessage)])
