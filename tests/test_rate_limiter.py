"""Tests for rate limiting functionality."""

import threading
from unittest.mock import patch

from gitlabber.rate_limiter import RateLimitedExecutor


class TestRateLimitedExecutor:
    """Test suite for RateLimitedExecutor."""

    def test_init_default(self):
        """Test default initialization."""
        limiter = RateLimitedExecutor()
        assert limiter.max_requests == 2000
        assert limiter.window_seconds == 3600
        assert len(limiter.requests) == 0

    def test_init_custom(self):
        """Test initialization with custom rate limit."""
        limiter = RateLimitedExecutor(max_requests_per_hour=100)
        assert limiter.max_requests == 100
        assert limiter.window_seconds == 3600

    def test_acquire_below_limit(self):
        """Test acquire when below rate limit."""
        limiter = RateLimitedExecutor(max_requests_per_hour=10)
        # Should not block
        limiter.acquire()
        assert len(limiter.requests) == 1

    def test_acquire_multiple_requests(self):
        """Test multiple acquires below limit."""
        limiter = RateLimitedExecutor(max_requests_per_hour=10)
        for _ in range(5):
            limiter.acquire()
        assert len(limiter.requests) == 5

    def test_acquire_at_limit_waits(self):
        """Test that acquire waits when rate limit is reached."""
        limiter = RateLimitedExecutor(max_requests_per_hour=2)
        
        # Mock time to simulate requests that haven't expired yet
        with patch.object(limiter, '_time_func') as mock_time, \
             patch('time.sleep') as mock_sleep:
            # First two requests at time 0 (at limit)
            limiter.requests = [0, 0]
            
            # Mock time to simulate waiting scenario
            # First call: check current time (100s after first request)
            # Second call: after sleep, time advances but requests still valid
            call_count = [0]
            def time_side_effect():
                call_count[0] += 1
                if call_count[0] == 1:
                    return 100  # Before sleep - requests still valid
                elif call_count[0] == 2:
                    return 101  # After first sleep iteration - still need to wait
                else:
                    # After multiple iterations, eventually requests expire
                    return 3700  # Requests expired, can proceed
            
            mock_time.side_effect = time_side_effect
            
            limiter.acquire()
            
            # Should have called sleep (waiting for rate limit)
            assert mock_sleep.called
            # Check that sleep was called with a value <= 1.0
            call_args = mock_sleep.call_args[0][0]
            assert call_args <= 1.0
            # After waiting, new request should be added
            # (old requests may be cleaned up if expired)
            assert len(limiter.requests) >= 1

    def test_acquire_expired_requests(self):
        """Test that expired requests are cleaned up."""
        limiter = RateLimitedExecutor(max_requests_per_hour=10)
        
        with patch.object(limiter, '_time_func') as mock_time:
            # Create old requests (outside the window)
            old_time = 0
            mock_time.return_value = old_time
            limiter.requests = [old_time, old_time]
            
            # Move time forward beyond the window
            new_time = old_time + limiter.window_seconds + 100
            mock_time.return_value = new_time
            
            # Acquire should clean up old requests
            limiter.acquire()
            
            # Old requests should be removed, only new one should remain
            assert len(limiter.requests) == 1
            assert limiter.requests[0] == new_time

    def test_acquire_thread_safety(self):
        """Test that acquire is thread-safe."""
        limiter = RateLimitedExecutor(max_requests_per_hour=100)
        results = []
        errors = []
        
        def worker():
            try:
                limiter.acquire()
                results.append(1)
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads
        threads = [threading.Thread(target=worker) for _ in range(50)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All threads should have succeeded
        assert len(errors) == 0
        assert len(results) == 50
        assert len(limiter.requests) == 50

    def test_decorator_functionality(self):
        """Test that the rate limiter works as a decorator."""
        limiter = RateLimitedExecutor(max_requests_per_hour=10)
        call_count = []
        
        @limiter
        def test_function(arg1, arg2=None):
            call_count.append((arg1, arg2))
            return arg1 + (arg2 or 0)
        
        # Call the decorated function
        result = test_function(5, arg2=3)
        
        # Function should have been called
        assert result == 8
        assert len(call_count) == 1
        assert call_count[0] == (5, 3)
        
        # Rate limiter should have recorded the call
        assert len(limiter.requests) == 1

    def test_decorator_with_keyword_args(self):
        """Test decorator with various argument patterns."""
        limiter = RateLimitedExecutor(max_requests_per_hour=10)
        
        @limiter
        def test_function(*args, **kwargs):
            return args, kwargs
        
        result = test_function(1, 2, a=3, b=4)
        assert result == ((1, 2), {'a': 3, 'b': 4})
        assert len(limiter.requests) == 1

    def test_wait_time_calculation(self):
        """Test wait time calculation when limit is reached."""
        limiter = RateLimitedExecutor(max_requests_per_hour=2)
        
        with patch.object(limiter, '_time_func') as mock_time, \
             patch('time.sleep') as mock_sleep:
            # Set up: 2 requests at time 0 (at limit)
            call_count = [0]
            def time_side_effect():
                call_count[0] += 1
                if call_count[0] == 1:
                    return 100  # Before sleep
                return 3700  # After sleep (requests expired)
            
            mock_time.side_effect = time_side_effect
            limiter.requests = [0, 0]
            
            # Should calculate wait time correctly
            # wait_time = 3600 - (100 - 0) = 3500, but we sleep max 1.0
            limiter.acquire()
            # Should have called sleep with max 1.0
            mock_sleep.assert_called()
            # Check that sleep was called with a value <= 1.0
            call_args = mock_sleep.call_args[0][0]
            assert call_args <= 1.0

    def test_immediate_expiry_path(self):
        """Test the path where oldest request has already expired (else branch at line 74)."""
        limiter = RateLimitedExecutor(max_requests_per_hour=2)
        
        with patch.object(limiter, '_time_func') as mock_time, \
             patch('time.sleep') as mock_sleep:
            # Set up: 2 requests at limit
            # We need to be at limit but with wait_time <= 0
            # This happens when oldest request has expired (now >= oldest + window_seconds)
            old_time = 0
            limiter.requests = [old_time, old_time]
            
            # Set time so that oldest request has expired (wait_time <= 0)
            # wait_time = window_seconds - (now - oldest) = 3600 - (3600 - 0) = 0
            call_count = [0]
            def time_side_effect():
                call_count[0] += 1
                if call_count[0] == 1:
                    # At limit, but wait_time = 0 (oldest just expired)
                    return limiter.window_seconds  # Exactly at expiry boundary
                else:
                    # After else branch cleanup
                    return limiter.window_seconds + 1
            
            mock_time.side_effect = time_side_effect
            
            # Should take the else branch (wait_time <= 0, line 72-75)
            limiter.acquire()
            
            # Should not have slept (else branch doesn't sleep)
            # The else branch recalculates and cleans up expired requests (line 74-75)
            assert not mock_sleep.called or len(mock_sleep.call_args_list) == 0
            # After cleanup, should have the new request
            assert len(limiter.requests) >= 1

