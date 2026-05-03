# tools/registry.py — Tool Registry (LangChain-based)
from langchain_core.tools import BaseTool
from typing import List, Dict, Any


class ToolRegistry:
    def __init__(self):
        self.tools: List[BaseTool] = []
        self._tool_map: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        """Add a tool to Boss"""
        self.tools.append(tool)
        self._tool_map[tool.name] = tool
        print(f"🔧 Registered tool: {tool.name}")
    
    def register_many(self, tools: List[BaseTool]):
        for tool in tools:
            self.register(tool)
    
    def get_tools(self) -> List[BaseTool]:
        return self.tools
    
    def execute(self, tool_name: str, args: Dict[str, Any]) -> Any:
        """Execute a tool by name (used by Boss Kernel)"""
        if tool_name not in self._tool_map:
            return f"Error: Tool '{tool_name}' not found."
        
        tool = self._tool_map[tool_name]
        try:
            return tool.invoke(args)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    def list_tools(self) -> List[str]:
        return [t.name for t in self.tools]
