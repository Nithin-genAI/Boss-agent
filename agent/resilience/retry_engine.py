# resilience/retry_engine.py — Auto-retry with exponential backoff
import time
import random
from typing import Callable, Any


class RetryEngine:
    """
    Retries failed operations with exponential backoff + jitter.
    Only retries on actual EXCEPTIONS, not on soft failure strings.
    """
    
    def __init__(self, max_retries: int = 2, base_delay: float = 1.0, max_delay: float = 8.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def execute(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute with retry logic. Only retries on raised exceptions."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = operation(*args, **kwargs)
                # Return ANY result that didn't throw an exception.
                # Tool results like "Could not find X" are valid responses,
                # not reasons to retry (which would re-launch Chrome).
                return result
                
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt) + random.uniform(0, 1), self.max_delay)
                    print(f"   🔄 Retry {attempt + 1}/{self.max_retries} after {delay:.1f}s ({str(e)[:50]})...")
                    time.sleep(delay)
        
        # All retries exhausted — return error string instead of crashing
        error_msg = str(last_error)[:200] if last_error else "Unknown error"
        return f"Tool failed after {self.max_retries} retries: {error_msg}"
