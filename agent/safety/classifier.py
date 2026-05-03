# safety/classifier.py — Tags actions by risk level
from enum import Enum
from typing import Dict, Any


class RiskLevel(Enum):
    READ = "read"              # Safe: list, read, search
    WRITE = "write"            # Caution: create, update, book
    DESTRUCTIVE = "destructive"  # Danger: delete, send, pay, rm


class ActionClassifier:
    """
    Classifies tool calls by risk level.
    """
    
    # Tool name → risk level
    TOOL_RISKS = {
        "get_system_info": RiskLevel.READ,
        "get_current_time": RiskLevel.READ,
        "read_file": RiskLevel.READ,
        "list_directory": RiskLevel.READ,
        "find_file": RiskLevel.READ,
        "search_file_content": RiskLevel.READ,
        "summarize_directory": RiskLevel.READ,
        "read_page_text": RiskLevel.READ,
        "take_screenshot": RiskLevel.READ,
        "take_browser_screenshot": RiskLevel.READ,
        
        "type_on_page": RiskLevel.WRITE,
        "navigate_to_url": RiskLevel.WRITE,
        "search_google": RiskLevel.WRITE,
        "click_on_page": RiskLevel.WRITE,
        "press_key": RiskLevel.WRITE,
        "open_application": RiskLevel.WRITE,
        "open_folder": RiskLevel.WRITE,
        "run_shell_command": RiskLevel.WRITE,
        
        "run_shell_command": RiskLevel.DESTRUCTIVE,  # Re-evaluated below
    }
    
    # Keywords in arguments that bump risk
    DESTRUCTIVE_KEYWORDS = ["rm", "delete", "remove", "sudo", "chmod", "drop", "truncate", "format", "send", "pay", "transfer", "cancel booking", "uninstall"]
    WRITE_KEYWORDS = ["create", "write", "update", "modify", "book", "reserve", "schedule", "submit", "post", "upload"]
    
    def classify(self, tool_name: str, args: Dict[str, Any]) -> RiskLevel:
        """Classify a tool call by risk."""
        base = self.TOOL_RISKS.get(tool_name, RiskLevel.WRITE)
        
        # Check argument content for risk keywords
        args_str = str(args).lower()
        
        if any(k in args_str for k in self.DESTRUCTIVE_KEYWORDS):
            return RiskLevel.DESTRUCTIVE
        
        if base == RiskLevel.READ and any(k in args_str for k in self.WRITE_KEYWORDS):
            return RiskLevel.WRITE
        
        return base
    
    def get_description(self, risk: RiskLevel) -> str:
        return {
            RiskLevel.READ: "This is safe — just reading information.",
            RiskLevel.WRITE: "This will make changes. I can undo some actions.",
            RiskLevel.DESTRUCTIVE: "This is destructive and may not be reversible."
        }.get(risk, "Unknown risk")
