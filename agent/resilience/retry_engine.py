# resilience/retry_engine.py — Auto-retry with exponential backoff
import time
import random
from typing import Callable, Any


class RetryEngine:
    """
    Retries failed operations with exponential backoff + jitter.
    """
    
    def __init__(self, max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 10.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def execute(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute with retry logic."""
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                result = operation(*args, **kwargs)
                # Check if result itself indicates failure
                if isinstance(result, str) and any(fail in result.lower() for fail in ["error", "failed", "blocked", "denied", "timeout", "not found"]):
                    if attempt < self.max_retries:
                        delay = min(self.base_delay * (2 ** attempt) + random.uniform(0, 1), self.max_delay)
                        print(f"   🔄 Retry {attempt + 1}/{self.max_retries} after {delay:.1f}s...")
                        time.sleep(delay)
                        continue
                return result
                
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    delay = min(self.base_delay * (2 ** attempt) + random.uniform(0, 1), self.max_delay)
                    print(f"   🔄 Retry {attempt + 1}/{self.max_retries} after {delay:.1f}s ({str(e)[:50]})...")
                    time.sleep(delay)
        
        # All retries exhausted
        raise last_error if last_error else Exception("Operation failed after all retries")
