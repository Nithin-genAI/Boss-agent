# resilience/circuit_breaker.py — Stop calling broken services
import time
from typing import Dict
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if recovered


class CircuitBreaker:
    """
    If a tool fails 3 times in 60 seconds, stop calling it for 30 seconds.
    """
    
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0, window_seconds: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.window_seconds = window_seconds
        
        self.states: Dict[str, CircuitState] = {}
        self.failures: Dict[str, list] = {}  # tool_name -> [timestamps]
        self.last_failure_time: Dict[str, float] = {}
    
    def can_execute(self, tool_name: str) -> bool:
        """Check if tool is allowed to execute."""
        now = time.time()
        
        # Clean old failures outside window
        if tool_name in self.failures:
            self.failures[tool_name] = [t for t in self.failures[tool_name] if now - t < self.window_seconds]
        
        state = self.states.get(tool_name, CircuitState.CLOSED)
        
        if state == CircuitState.OPEN:
            # Check if recovery timeout passed
            last_fail = self.last_failure_time.get(tool_name, 0)
            if now - last_fail >= self.recovery_timeout:
                self.states[tool_name] = CircuitState.HALF_OPEN
                print(f"   🔧 Circuit for {tool_name}: HALF_OPEN (testing recovery)")
                return True
            print(f"   ⛔ Circuit for {tool_name}: OPEN (blocked)")
            return False
        
        return True
    
    def record_success(self, tool_name: str):
        """Mark tool as working."""
        if self.states.get(tool_name) == CircuitState.HALF_OPEN:
            self.states[tool_name] = CircuitState.CLOSED
            self.failures[tool_name] = []
            print(f"   ✅ Circuit for {tool_name}: CLOSED (recovered)")
    
    def record_failure(self, tool_name: str):
        """Mark tool as potentially failing."""
        now = time.time()
        
        if tool_name not in self.failures:
            self.failures[tool_name] = []
        
        self.failures[tool_name].append(now)
        self.last_failure_time[tool_name] = now
        
        if len(self.failures[tool_name]) >= self.failure_threshold:
            self.states[tool_name] = CircuitState.OPEN
            print(f"   ⛔ Circuit for {tool_name}: OPEN (too many failures)")
