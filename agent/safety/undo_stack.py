# safety/undo_stack.py — Reversible action tracking
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class UndoableAction:
    action_id: str
    tool_name: str
    args: Dict[str, Any]
    result: Any
    undo_tool: Optional[str] = None  # Tool to call to reverse this
    undo_args: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""


class UndoStack:
    """
    Stack of actions that can be undone.
    """
    
    def __init__(self, max_size: int = 50):
        self.stack: List[UndoableAction] = []
        self.max_size = max_size
    
    def push(self, tool_name: str, args: Dict, result: Any, registry) -> None:
        """Record an action and infer how to undo it."""
        import uuid
        from datetime import datetime
        
        action_id = str(uuid.uuid4())[:8]
        
        # Infer undo logic
        undo_tool, undo_args = self._infer_undo(tool_name, args, result, registry)
        
        action = UndoableAction(
            action_id=action_id,
            tool_name=tool_name,
            args=args,
            result=result,
            undo_tool=undo_tool,
            undo_args=undo_args,
            timestamp=datetime.now().isoformat()
        )
        
        self.stack.append(action)
        if len(self.stack) > self.max_size:
            self.stack.pop(0)
        
        print(f"   📝 Recorded action {action_id}: {tool_name}")
    
    def undo_last(self, registry) -> str:
        """Undo the most recent action."""
        if not self.stack:
            return "Nothing to undo."
        
        action = self.stack.pop()
        
        if not action.undo_tool:
            return f"Cannot undo {action.tool_name} — no reverse action available."
        
        try:
            result = registry.execute(action.undo_tool, action.undo_args)
            return f"Undid {action.tool_name} (action {action.action_id}). {result}"
        except Exception as e:
            return f"Failed to undo {action.tool_name}: {str(e)}"
    
    def get_history(self) -> List[Dict]:
        return [
            {
                "id": a.action_id,
                "tool": a.tool_name,
                "args": a.args,
                "undoable": a.undo_tool is not None
            }
            for a in reversed(self.stack[-10:])
        ]
    
    def _infer_undo(self, tool_name: str, args: Dict, result: Any, registry) -> tuple:
        """Infer how to undo an action."""
        # File creation → delete file
        if tool_name == "run_shell_command":
            cmd = args.get("command", "")
            if "touch" in cmd or "mkdir" in cmd:
                created = cmd.split()[-1]
                return "run_shell_command", {"command": f"rm -rf {created}"}
            if "echo" in cmd and ">" in cmd:
                file = cmd.split(">")[-1].strip()
                return "run_shell_command", {"command": f"rm {file}"}
        
        # Browser navigation → go back (if possible)
        if tool_name == "navigate_to_url":
            return None, {}  # Can't easily undo navigation
        
        # App open → close app (macOS)
        if tool_name == "open_application":
            app = args.get("app_name", "")
            return "run_shell_command", {"command": f"pkill '{app}'"}
        
        # Default: not undoable
        return None, {}
