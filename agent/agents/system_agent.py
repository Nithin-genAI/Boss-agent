# agents/system_agent.py — Specialist for computer operations
import os
from typing import Dict, Any


class SystemAgent:
    """
    Handles: files, directories, apps, screenshots, shell commands.
    """
    
    def __init__(self, registry):
        self.registry = registry
    
    def execute(self, instruction: str) -> Dict[str, Any]:
        """Parse and execute system instructions."""
        inst_lower = instruction.lower()
        
        # File read
        if "read" in inst_lower and ("file" in inst_lower or "." in instruction):
            path = self._extract_path(instruction)
            return self._read_file(path)
        
        # List directory
        if "list" in inst_lower or "show" in inst_lower and ("files" in inst_lower or "folder" in inst_lower or "directory" in inst_lower):
            path = self._extract_path(instruction) or "."
            return self._list_directory(path)
        
        # Open app
        if "open" in inst_lower and any(app in inst_lower for app in ["safari", "chrome", "vscode", "code", "calculator", "notes", "terminal"]):
            app = self._extract_app(inst_lower)
            return self._open_app(app)
        
        # Screenshot
        if "screenshot" in inst_lower or "capture" in inst_lower:
            return self._screenshot()
        
        # Shell
        if "run" in inst_lower or "execute" in inst_lower or "command" in inst_lower:
            cmd = instruction.replace("run", "").replace("execute", "").replace("command", "").strip()
            return self._shell(cmd)
        
        # Find file
        if "find" in inst_lower and ("file" in inst_lower or "." in instruction):
            name = instruction.replace("find", "").replace("file", "").strip()
            return self._find_file(name)
        
        return {"success": False, "error": "Unknown system instruction"}
    
    def _extract_path(self, instruction: str) -> str:
        # Try to find path-like strings
        import re
        paths = re.findall(r'[~/]?[\w/.-]+\.\w+|[~/][\w/.-]+', instruction)
        return paths[0] if paths else ""
    
    def _extract_app(self, instruction: str) -> str:
        apps = {
            "safari": "Safari",
            "chrome": "Google Chrome",
            "vscode": "Visual Studio Code",
            "code": "Visual Studio Code",
            "calculator": "Calculator",
            "notes": "Notes",
            "terminal": "Terminal",
        }
        for key, val in apps.items():
            if key in instruction:
                return val
        return "Safari"
    
    def _read_file(self, path: str) -> Dict[str, Any]:
        r = self.registry.execute("read_file", {"file_path": path})
        return {"success": True, "action": "read_file", "path": path, "content": r}
    
    def _list_directory(self, path: str) -> Dict[str, Any]:
        r = self.registry.execute("list_directory", {"dir_path": path})
        return {"success": True, "action": "list_directory", "path": path, "content": r}
    
    def _open_app(self, app: str) -> Dict[str, Any]:
        r = self.registry.execute("open_application", {"app_name": app})
        return {"success": True, "action": "open_app", "app": app, "result": r}
    
    def _screenshot(self) -> Dict[str, Any]:
        r = self.registry.execute("take_screenshot", {})
        return {"success": True, "action": "screenshot", "result": r}
    
    def _shell(self, cmd: str) -> Dict[str, Any]:
        r = self.registry.execute("run_shell_command", {"command": cmd})
        return {"success": True, "action": "shell", "command": cmd, "result": r}
    
    def _find_file(self, name: str) -> Dict[str, Any]:
        r = self.registry.execute("find_file", {"filename": name})
        return {"success": True, "action": "find_file", "name": name, "result": r}
