"""Rate limiting utilities for API calls."""

from __future__ import annotations

import threading
import time


class RateLimitedExecutor:
    """Thread-safe rate limiter for API calls.
    
    This class implements a simple rate limiting mechanism that tracks
    the number of requests made within a time window (1 hour by default).
    It ensures that concurrent API calls from multiple threads respect
    the rate limit.
    
    Example:
        >>> limiter = RateLimitedExecutor(max_requests_per_hour=2000)
        >>> limiter.acquire()  # Blocks if limit reached
        >>> # Make API call
    """

    def __init__(self, max_requests_per_hour: int = 2000):
        """Initialize the rate limiter.
        
        Args:
            max_requests_per_hour: Maximum number of requests allowed per hour
        """
        self.max_requests = max_requests_per_hour
        self.requests: list[float] = []
        self.lock = threading.Lock()
        self.window_seconds = 3600  # 1 hour
        # Use monotonic time for better accuracy and to avoid clock adjustments
        self._time_func = time.monotonic

    def acquire(self) -> None:
        """Acquire permission to make an API call.
        
        This method blocks if the rate limit has been reached, waiting
        until enough time has passed for the oldest request to expire.
        
        Thread-safe: Multiple threads can call this concurrently.
        """
        with self.lock:
            now = self._time_func()
            
            # Remove requests older than the time window (use deque for O(1) popleft)
            cutoff_time = now - self.window_seconds
            # Keep only recent requests
            self.requests = [req_time for req_time in self.requests if req_time > cutoff_time]
            
            # Wait if limit reached
            while len(self.requests) >= self.max_requests:
                # Calculate wait time until oldest request expires
                oldest_request = self.requests[0]
                wait_time = self.window_seconds - (now - oldest_request)
                
                if wait_time > 0:
                    # Release lock while waiting to allow other threads to proceed
                    # when their requests expire
                    self.lock.release()
                    try:
                        time.sleep(min(wait_time, 1.0))  # Sleep in small increments
                    finally:
                        self.lock.acquire()
                    
                    # Recalculate after sleep
                    now = self._time_func()
                    cutoff_time = now - self.window_seconds
                    self.requests = [req_time for req_time in self.requests if req_time > cutoff_time]
                else:
                    # Oldest request should have expired, recalculate
                    cutoff_time = now - self.window_seconds
                    self.requests = [req_time for req_time in self.requests if req_time > cutoff_time]
            
            # Record this request
            self.requests.append(now)

    def __call__(self, func):
        """Decorator for rate-limited API calls.
        
        Args:
            func: Function to wrap with rate limiting
            
        Returns:
            Wrapped function that acquires rate limit before calling func
        """
        def wrapper(*args, **kwargs):
            self.acquire()
            return func(*args, **kwargs)
        return wrapper

