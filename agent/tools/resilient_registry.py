# tools/resilient_registry.py — ToolRegistry wrapped with resilience
from tools.registry import ToolRegistry
from resilience.retry_engine import RetryEngine
from resilience.circuit_breaker import CircuitBreaker
from resilience.fallback import FallbackChain
from resilience.error_translator import ErrorTranslator


class ResilientRegistry:
    """
    Drop-in replacement for ToolRegistry.
    Adds retry, circuit breaker, fallback, and error translation.
    """
    
    def __init__(self, base_registry: ToolRegistry = None):
        self.base = base_registry or ToolRegistry()
        self.retry = RetryEngine(max_retries=2, base_delay=1.0)
        self.circuit = CircuitBreaker(failure_threshold=3, recovery_timeout=30.0)
        self.fallback = FallbackChain()
        self.translator = ErrorTranslator()
        self.mock_mode = False  # Set True for demo when APIs fail
    
    def register(self, tool):
        self.base.register(tool)
    
    def register_many(self, tools):
        self.base.register_many(tools)
    
    def get_tools(self):
        return self.base.get_tools()
    
    def list_tools(self):
        return self.base.list_tools()
    
    def execute(self, tool_name: str, args: dict) -> any:
        """Execute with full resilience stack."""
        print(f"   ⚡ Resilient execute: {tool_name}")
        
        # 0. Force mock mode
        if self.mock_mode:
            mock = self.fallback.get_mock(tool_name, str(args))
            print(f"   🎭 Demo Mode — injecting mock data")
            return self.translator.translate_success(tool_name, mock)
        
        # 1. Circuit breaker check
        if not self.circuit.can_execute(tool_name):
            # Use mock
            mock = self.fallback.get_mock(tool_name, str(args))
            print(f"   📦 Circuit open — using mock: {mock}")
            return self.translator.translate_success(tool_name, mock)
        
        # 2. Execute with retry
        try:
            result = self.retry.execute(self.base.execute, tool_name, args)
            self.circuit.record_success(tool_name)
            
            # Check if result is actually a failure
            if isinstance(result, str) and any(fail in result.lower() for fail in ["error", "failed", "denied", "blocked", "not found"]):
                raise Exception(result)
            
            print(f"   ✅ {tool_name} succeeded")
            return self.translator.translate_success(tool_name, result)
            
        except Exception as e:
            self.circuit.record_failure(tool_name)
            error_msg = self.translator.translate(str(e), tool_name)
            print(f"   ❌ {tool_name} failed: {error_msg}")
            
            # 3. Try fallback tool
            fallback_tool, fallback_args = self.fallback.get_fallback(tool_name, args)
            if fallback_tool:
                print(f"   🔄 Trying fallback: {fallback_tool}")
                try:
                    result = self.base.execute(fallback_tool, fallback_args)
                    return self.translator.translate_success(fallback_tool, result)
                except Exception as e2:
                    print(f"   ❌ Fallback also failed: {e2}")
            
            # 4. Return translated error
            return error_msg
    
    def enable_mock_mode(self):
        self.mock_mode = True
        print("   🎭 Mock mode ENABLED")
    
    def disable_mock_mode(self):
        self.mock_mode = False
        print("   🎭 Mock mode DISABLED")
