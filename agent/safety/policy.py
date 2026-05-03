# safety/policy.py — Configurable safety rules
from typing import List, Dict


class SafetyPolicy:
    """
    Hard rules that cannot be overridden.
    """
    
    BLOCKED_COMMANDS = [
        "rm -rf /", "rm -rf ~", "rm -rf /*", "sudo rm",
        "mkfs", "dd if=", ":(){:|:&};:", "del /f /s /q",
        "format c:", "shutdown", "reboot", "halt",
    ]
    
    BLOCKED_PATHS = [
        "/etc/passwd", "/etc/shadow", "/etc/hosts",
        "~/.ssh/id_rsa", "~/.ssh/id_ed25519",
        "/var/log", "/System", "/usr/bin",
    ]
    
    REQUIRE_EXPLICIT_CONFIRM = [
        "run_shell_command",  # When destructive
    ]
    
    def check(self, tool_name: str, args: Dict) -> tuple:
        """
        Returns: (allowed: bool, reason: str)
        """
        args_str = str(args).lower()
        
        # Check blocked commands
        for blocked in self.BLOCKED_COMMANDS:
            if blocked.lower() in args_str:
                return False, f"POLICY BLOCK: '{blocked}' is permanently forbidden."
        
        # Check blocked paths
        for path in self.BLOCKED_PATHS:
            expanded = path.replace("~", "/home")  # Rough expansion
            if path.lower() in args_str or expanded.lower() in args_str:
                return False, f"POLICY BLOCK: Access to '{path}' is forbidden."
        
        return True, ""
    
    def is_explicit_confirm_required(self, tool_name: str, args: Dict) -> bool:
        """Check if this specific call needs typed YES."""
        if tool_name in self.REQUIRE_EXPLICIT_CONFIRM:
            cmd = str(args.get("command", "")).lower()
            dangerous = ["rm", "delete", "remove", "sudo", "chmod", "chown", "mkfs", "dd", "curl", "wget"]
            if any(d in cmd.split() for d in dangerous):
                return True
        return False
