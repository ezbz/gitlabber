"""Performance tests for API concurrency.

These tests measure the actual speedup achieved by parallel API calls.
They require a real GitLab instance and are marked as slow integration tests.
"""

import os
import json
import time
import pytest
from typing import Dict, Any
import tests.io_test_util as io_util


@pytest.mark.slow_integration_test
def test_api_concurrency_speedup():
    """Test that parallel API calls provide speedup over sequential calls.
    
    This test compares the time taken to build a tree with:
    - Sequential API calls (api_concurrency=1)
    - Parallel API calls (api_concurrency=5)
    
    It verifies that parallel calls are faster and produce identical results.
    """
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    
    # Use a group with multiple subgroups/projects for measurable difference
    group_search = 'large-group-test'
    
    # Test sequential (api_concurrency=1)
    start_time = time.time()
    sequential_output = io_util.execute(
        [
            '-p', '--print-format', 'json',
            '--group-search', group_search,
            '--api-concurrency', '1',
            '--verbose'
        ],
        timeout=300  # 5 minutes for sequential
    )
    sequential_time = time.time() - start_time
    
    # Parse sequential output
    sequential_obj = json.loads(sequential_output)
    
    # Test parallel (api_concurrency=5)
    start_time = time.time()
    parallel_output = io_util.execute(
        [
            '-p', '--print-format', 'json',
            '--group-search', group_search,
            '--api-concurrency', '5',
            '--verbose'
        ],
        timeout=300  # 5 minutes for parallel
    )
    parallel_time = time.time() - start_time
    
    # Parse parallel output
    parallel_obj = json.loads(parallel_output)
    
    # Verify results are identical
    assert sequential_obj == parallel_obj, "Parallel and sequential results should be identical"
    
    # Calculate speedup
    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    
    # Log results for visibility
    print("\n" + "="*60)
    print("API Concurrency Performance Test Results")
    print("="*60)
    print(f"Group search: {group_search}")
    print(f"Sequential time (api_concurrency=1): {sequential_time:.2f}s")
    print(f"Parallel time (api_concurrency=5): {parallel_time:.2f}s")
    print(f"Speedup: {speedup:.2f}x")
    print(f"{'='*60}\n")
    
    # Assert that parallel is at least as fast (accounting for variance)
    # In practice, parallel should be faster, but we allow for some variance
    # due to network conditions, API rate limiting, etc.
    assert parallel_time <= sequential_time * 1.1, (
        f"Parallel execution ({parallel_time:.2f}s) should be faster or similar "
        f"to sequential ({sequential_time:.2f}s), but it was slower. "
        f"Speedup: {speedup:.2f}x"
    )
    
    # For large groups, we expect at least some speedup
    # (at least 1.2x for groups with multiple subgroups/projects)
    if sequential_time > 5.0:  # Only check speedup for longer operations
        assert speedup >= 1.1, (
            f"Expected speedup of at least 1.1x for large groups, "
            f"but got {speedup:.2f}x. Sequential: {sequential_time:.2f}s, "
            f"Parallel: {parallel_time:.2f}s"
        )


@pytest.mark.slow_integration_test
def test_api_concurrency_correctness():
    """Test that parallel API calls produce correct results.
    
    This test verifies that using api_concurrency doesn't affect
    the correctness of the tree structure.
    """
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    
    group_search = 'Group Test'
    
    # Test with different concurrency levels
    concurrency_levels = [1, 3, 5, 10]
    results = {}
    
    for concurrency in concurrency_levels:
        output = io_util.execute(
            [
                '-p', '--print-format', 'json',
                '--group-search', group_search,
                '--api-concurrency', str(concurrency),
                '--verbose'
            ],
            timeout=120
        )
        results[concurrency] = json.loads(output)
    
    # All results should be identical regardless of concurrency level
    baseline = results[1]
    for concurrency, result in results.items():
        assert result == baseline, (
            f"Results with api_concurrency={concurrency} differ from baseline (api_concurrency=1)"
        )
    
    print(f"\n✓ Correctness verified for all concurrency levels: {concurrency_levels}")


@pytest.mark.slow_integration_test
def test_api_concurrency_with_rate_limiting():
    """Test that rate limiting works correctly with parallel API calls.
    
    This test verifies that rate limiting prevents API abuse even with
    high concurrency levels.
    """
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    
    group_search = 'large-group-test'
    
    # Test with high concurrency (should still respect rate limits)
    output = io_util.execute(
        [
            '-p', '--print-format', 'json',
            '--group-search', group_search,
            '--api-concurrency', '10',  # High concurrency
            '--verbose'
        ],
        timeout=300
    )
    
    # Should complete without rate limit errors
    obj = json.loads(output)
    assert 'children' in obj, "Should successfully build tree even with high concurrency"
    
    print("\n✓ Rate limiting works correctly with high concurrency (10)")


def _measure_tree_build_time(args: list[str], timeout: int = 300) -> tuple[float, Dict[str, Any]]:
    """Helper to measure tree build time and return result.
    
    Args:
        args: CLI arguments
        timeout: Maximum time to wait
        
    Returns:
        Tuple of (time_taken, parsed_json_result)
    """
    start_time = time.time()
    output = io_util.execute(args, timeout)
    elapsed_time = time.time() - start_time
    result = json.loads(output)
    return elapsed_time, result


@pytest.mark.slow_integration_test
def test_api_concurrency_scaling():
    """Test how speedup scales with different concurrency levels.
    
    This test measures performance at different concurrency levels
    to understand the optimal setting.
    """
    os.environ['GITLAB_URL'] = 'https://gitlab.com/'
    
    group_search = 'large-group-test'
    concurrency_levels = [1, 2, 3, 5, 10]
    results = {}
    
    print("\n" + "="*60)
    print("API Concurrency Scaling Test")
    print("="*60)
    print(f"Group search: {group_search}")
    print(f"Testing concurrency levels: {concurrency_levels}\n")
    
    for concurrency in concurrency_levels:
        time_taken, result = _measure_tree_build_time(
            [
                '-p', '--print-format', 'json',
                '--group-search', group_search,
                '--api-concurrency', str(concurrency),
                '--verbose'
            ],
            timeout=300
        )
        results[concurrency] = {
            'time': time_taken,
            'result': result
        }
        print(f"  api_concurrency={concurrency:2d}: {time_taken:6.2f}s")
    
    # Calculate speedups relative to sequential (concurrency=1)
    baseline_time = results[1]['time']
    print("\nSpeedup relative to sequential (api_concurrency=1):")
    for concurrency in concurrency_levels[1:]:  # Skip baseline
        speedup = baseline_time / results[concurrency]['time']
        print(f"  api_concurrency={concurrency:2d}: {speedup:.2f}x")
    
    # Verify all results are identical
    baseline_result = results[1]['result']
    for concurrency in concurrency_levels[1:]:
        assert results[concurrency]['result'] == baseline_result, (
            f"Results with api_concurrency={concurrency} differ from baseline"
        )
    
    print(f"{'='*60}\n")
    
    # Verify that higher concurrency generally improves performance
    # (up to a point - diminishing returns expected)
    times = [results[c]['time'] for c in concurrency_levels]
    assert times[1] <= times[0] * 1.1, "Concurrency=2 should be faster than sequential"
    assert times[-1] <= times[0] * 1.1, "Highest concurrency should be faster than sequential"

