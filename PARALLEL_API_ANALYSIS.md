# Parallel API Calls with Rate Limiting - Design Analysis

## Current Architecture

### Current Sequential API Call Pattern

```
build_from_gitlab()
  └─> groups.list(get_all=True)  # 1 API call - sequential
       └─> For each group (sequential loop):
            ├─> get_subgroups(group)
            │    └─> subgroups.list(get_all=True)  # 1 API call per group
            │         └─> For each subgroup (sequential loop):
            │              └─> groups.get(subgroup_id)  # 1 API call per subgroup
            │                   └─> Recursively get_subgroups() + get_projects()
            └─> get_projects(group)
                 ├─> projects.list(get_all=True)  # 1 API call per group
                 └─> shared_projects.list(get_all=True)  # 1 API call per group (if enabled)
```

### Current Performance Characteristics

**Sequential execution:**
- Groups processed one at a time
- For each group: subgroups → projects (sequential)
- For each subgroup: details fetched sequentially
- **Total time**: Sum of all API call latencies

**Example for 10 groups with 5 subgroups each:**
- 1 call: `groups.list()`
- 10 calls: `subgroups.list()` (one per group)
- 50 calls: `groups.get(id)` (one per subgroup)
- 10 calls: `projects.list()` (one per group)
- **Total: ~71 API calls, all sequential**

## Parallelization Opportunities

### Level 1: Parallel Group Processing
**Concept:** Process multiple groups concurrently

**Implementation:**
- Use `ThreadPoolExecutor` or `asyncio`
- Process groups in parallel batches
- Each group still fetches subgroups/projects sequentially

**Efficiency:** ⭐⭐⭐⭐ (High - significant speedup)

**Example:**
```python
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(self._process_group, group, root)
        for group in groups
    ]
    for future in concurrent.futures.as_completed(futures):
        future.result()
```

### Level 2: Parallel Subgroups + Projects
**Concept:** For each group, fetch subgroups and projects in parallel

**Implementation:**
- Within `get_subgroups()`, fetch subgroup details in parallel
- Fetch projects and subgroups concurrently for same group

**Efficiency:** ⭐⭐⭐ (Medium - moderate speedup)

**Example:**
```python
def get_subgroups_and_projects(self, group, parent):
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Fetch subgroups and projects in parallel
        subgroup_future = executor.submit(self.get_subgroups, group, parent)
        project_future = executor.submit(self.get_projects, group, parent)
        subgroup_future.result()
        project_future.result()
```

### Level 3: Parallel Subgroup Details
**Concept:** Fetch all subgroup details in parallel

**Implementation:**
- Collect all subgroup IDs first
- Fetch all subgroup details in parallel batch

**Efficiency:** ⭐⭐⭐⭐ (High - significant speedup for deep hierarchies)

**Example:**
```python
def get_subgroups(self, group, parent):
    subgroups = group.subgroups.list(get_all=True)
    # Fetch all subgroup details in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(self.gitlab.groups.get, sg.id): sg
            for sg in subgroups
        }
        for future in concurrent.futures.as_completed(futures):
            subgroup = future.result()
            # Process subgroup...
```

### Level 4: Full Parallelization
**Concept:** Combine all levels - parallel groups, parallel subgroups/projects, parallel details

**Efficiency:** ⭐⭐⭐⭐⭐ (Very High - maximum speedup)

**Complexity:** ⭐⭐⭐⭐⭐ (Very High - complex coordination)

## Rate Limiting Considerations

### GitLab Rate Limits

**GitLab.com:**
- Authenticated: 2,000 requests/hour
- Unauthenticated: 20 requests/hour

**Self-hosted:**
- Configurable, typically 600-2,000 requests/hour
- Can be higher for on-premise

### Rate Limit Headers

GitLab API returns rate limit info in headers:
- `RateLimit-Limit`: Maximum requests per hour
- `RateLimit-Remaining`: Remaining requests
- `RateLimit-Reset`: Unix timestamp when limit resets

### python-gitlab Rate Limiting

**Current behavior:**
- `python-gitlab` library may handle some rate limiting
- But it's not guaranteed to be thread-safe
- Multiple threads could exceed limits

**Need to implement:**
- Thread-safe rate limiter
- Respect rate limit headers
- Exponential backoff on 429 (Too Many Requests)
- Queue requests when limit reached

## Implementation Strategy

### Option 1: ThreadPoolExecutor with Rate Limiter (Recommended)

**Architecture:**
```python
class RateLimitedExecutor:
    """Thread-safe rate limiter for API calls."""
    
    def __init__(self, max_requests_per_hour: int = 2000):
        self.max_requests = max_requests_per_hour
        self.requests = []
        self.lock = threading.Lock()
    
    def acquire(self):
        """Acquire permission to make API call."""
        with self.lock:
            # Remove requests older than 1 hour
            now = time.time()
            self.requests = [r for r in self.requests if now - r < 3600]
            
            # Wait if limit reached
            while len(self.requests) >= self.max_requests:
                sleep_time = 3600 - (now - self.requests[0])
                time.sleep(sleep_time)
                now = time.time()
                self.requests = [r for r in self.requests if now - r < 3600]
            
            self.requests.append(now)
    
    def __call__(self, func):
        """Decorator for rate-limited API calls."""
        def wrapper(*args, **kwargs):
            self.acquire()
            return func(*args, **kwargs)
        return wrapper
```

**Integration:**
```python
class GitlabTreeBuilder:
    def __init__(self, ..., api_concurrency: int = 5):
        self.rate_limiter = RateLimitedExecutor(max_requests_per_hour=2000)
        self.api_concurrency = api_concurrency
    
    def build_from_gitlab(self, base_url: str, group_search: Optional[str]) -> Node:
        groups = self.gitlab.groups.list(...)
        
        # Process groups in parallel
        with ThreadPoolExecutor(max_workers=self.api_concurrency) as executor:
            futures = [
                executor.submit(self._process_group_with_rate_limit, group, root)
                for group in groups
            ]
            for future in concurrent.futures.as_completed(futures):
                future.result()
    
    def _process_group_with_rate_limit(self, group, root):
        self.rate_limiter.acquire()
        return self._process_group(group, root)
```

**Pros:**
- Simple to implement
- Thread-safe
- Respects rate limits
- Works with existing code

**Cons:**
- Fixed rate limit (doesn't read headers)
- May be conservative (waits even when limit not reached)

### Option 2: Header-Aware Rate Limiter (Advanced)

**Architecture:**
```python
class HeaderAwareRateLimiter:
    """Rate limiter that reads GitLab rate limit headers."""
    
    def __init__(self, gitlab_client):
        self.gitlab = gitlab_client
        self.lock = threading.Lock()
        self.remaining = None
        self.reset_time = None
    
    def acquire(self):
        """Acquire permission, checking headers from last request."""
        with self.lock:
            if self.remaining is not None and self.remaining <= 0:
                # Wait until reset time
                wait_time = self.reset_time - time.time()
                if wait_time > 0:
                    time.sleep(wait_time)
            
            # Make API call (will update headers)
            # Note: This requires wrapping python-gitlab requests
    
    def update_from_headers(self, headers):
        """Update rate limit info from response headers."""
        with self.lock:
            self.remaining = int(headers.get('RateLimit-Remaining', 2000))
            self.reset_time = int(headers.get('RateLimit-Reset', time.time() + 3600))
```

**Pros:**
- Dynamic rate limit detection
- More efficient (uses actual limits)
- Respects server-side limits

**Cons:**
- Complex (requires intercepting HTTP responses)
- May need to modify python-gitlab usage
- Harder to test

### Option 3: Token Bucket Algorithm

**Architecture:**
```python
class TokenBucketRateLimiter:
    """Token bucket algorithm for rate limiting."""
    
    def __init__(self, rate: int, capacity: int):
        self.rate = rate  # tokens per second
        self.capacity = capacity  # max tokens
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def acquire(self, tokens: int = 1):
        """Acquire tokens, waiting if necessary."""
        with self.lock:
            now = time.time()
            # Add tokens based on elapsed time
            elapsed = now - self.last_update
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_update = now
            
            # Wait if not enough tokens
            if self.tokens < tokens:
                wait_time = (tokens - self.tokens) / self.rate
                time.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= tokens
```

**Pros:**
- Smooth rate limiting (no bursts)
- Configurable rate
- Efficient

**Cons:**
- More complex than simple counter
- May be overkill for this use case

## Recommended Implementation

### Phase 1: Basic Parallelization (IMPLEMENTED ✅)

**Scope:**
- ✅ Parallel group processing
- ✅ Simple rate limiter (fixed limit)
- ✅ Thread-safe progress reporting

**Changes Implemented:**
1. ✅ Add `api_concurrency` parameter to `GitlabTreeBuilder` (separate from existing `concurrency` for git ops)
2. ✅ Add `api_concurrency` to `GitlabberConfig` and `GitlabberSettings`
3. ✅ Add `--api-concurrency` CLI option
4. ✅ Implement simple `RateLimitedExecutor`
5. ✅ Use `ThreadPoolExecutor` for group processing
6. ✅ Add rate limit configuration option

**Important:** This does NOT change the existing `concurrency` parameter, which continues to control git operations only.

**Efficiency:** ⭐⭐⭐ (Medium - Limited gain for small number of groups, but enables Phase 2)

**Complexity:** ⭐⭐ (Low - straightforward)

**Real-World Results:**
- **Test case**: 3 top-level groups
- **Phase 1 speedup**: Minimal (~0-5% improvement)
- **Reason**: With only 3 groups, parallelization overhead negates benefits
- **Phase 2 needed**: Real bottleneck is within groups (21 subgroups, many projects)

### Phase 2: Enhanced Parallelization (IMPLEMENTED ✅)

**Scope:**
- ✅ Parallel subgroups + projects within groups
- ✅ Parallel subgroup detail fetching
- ⏸️ Header-aware rate limiting (deferred - not needed)

**Changes Implemented:**
1. ✅ Parallelize `get_subgroups()` and `get_projects()` within each group
2. ✅ Batch fetch subgroup details in parallel (all subgroup details fetched concurrently)
3. ⏸️ Header-aware rate limiter (deferred - simple rate limiter sufficient)

**Efficiency:** ⭐⭐⭐⭐⭐ (Very High - Expected 5-10x speedup for instances with many subgroups)

**Complexity:** ⭐⭐⭐ (Medium - implemented with careful thread coordination)

**Why Phase 1 Showed Minimal Gain:**
- **Test case had only 3 top-level groups** - not enough parallelism at group level
- **Real bottleneck**: Fetching 21 subgroups sequentially within "Many Subgroups"
- **Phase 2 addresses this**: Parallelizes subgroup detail fetching (21 subgroups fetched concurrently)
- **Expected improvement**: With 21 subgroups, Phase 2 should provide ~5-10x speedup

**Implementation Details:**
- `_process_group()`: Parallelizes `get_subgroups()` and `get_projects()` (2 threads)
- `get_subgroups()`: Batch fetches all subgroup details in parallel (up to `api_concurrency` threads)
- `_fetch_subgroup_detail()`: Helper method for parallel subgroup detail fetching
- `_process_subgroup()`: Processes fetched subgroup and recursively fetches children

## Efficiency Analysis

### Current Performance (Sequential)

**Example: 10 groups, 5 subgroups each, 20 projects per group:**
- API calls: ~71 calls
- Average latency: 200ms per call
- **Total time: ~14 seconds**

### With Parallel Group Processing (Phase 1)

**Same example with 5 concurrent workers:**
- Groups processed in 2 batches (5 + 5)
- **Total time: ~3-4 seconds** (3-4x speedup)

### With Full Parallelization (Phase 2)

**Same example with full parallelization:**
- All independent operations parallel
- **Total time: ~1-2 seconds** (7-14x speedup)

### Real-World Impact

**Large GitLab instance (100 groups, 10 subgroups each):**
- Sequential: ~5-10 minutes
- Phase 1: ~1-2 minutes (5x speedup)
- Phase 2: ~30-60 seconds (10x speedup)

## Configuration

### Important: Distinction from Existing `concurrency` Parameter

**Current `concurrency` parameter:**
- Used for **git operations** (cloning/pulling repositories)
- Located in `GitlabberConfig.concurrency`
- CLI option: `-c/--concurrency`
- Controls `GitSyncManager` thread pool for git commands

**New `api_concurrency` parameter:**
- Used for **API calls** (fetching groups/projects from GitLab API)
- Separate from git operations concurrency
- Controls `GitlabTreeBuilder` thread pool for API requests

**Why separate?**
- Different resource constraints (API rate limits vs. disk I/O)
- Different optimal values (API: 5-10, Git: 1-20+)
- Independent tuning for different phases

### New Configuration Options

```python
class GitlabberConfig:
    # ... existing fields ...
    concurrency: int = Field(1, gt=0)  # Existing: concurrent git operations
    api_concurrency: int = Field(5, ge=1, le=20)  # New: parallel API calls
    api_rate_limit: Optional[int] = Field(None, ge=1)  # Requests per hour (None = auto-detect)
```

### CLI Options

```python
concurrency: Optional[int] = typer.Option(
    None,
    "-c",
    "--concurrency",
    help="Number of concurrent git operations (default: 1)"
)

api_concurrency: Optional[int] = typer.Option(
    None,
    "--api-concurrency",
    help="Number of concurrent API calls (default: 5)"
)
```

### Environment Variables

```python
class GitlabberSettings:
    # ... existing fields ...
    concurrency: Optional[int] = None  # Existing: GITLABBER_GIT_CONCURRENCY
    api_concurrency: Optional[int] = None  # New: GITLABBER_API_CONCURRENCY
```

**Note:** The existing `concurrency` parameter remains unchanged and continues to control git operations only.

### How They Work Together

**Workflow:**
1. **Tree Building Phase** (uses `api_concurrency`):
   - Fetch groups, subgroups, projects from GitLab API
   - Parallel API calls controlled by `api_concurrency` (default: 5)
   - Rate limiting applied to prevent API abuse

2. **Git Sync Phase** (uses `concurrency`):
   - Clone/pull repositories based on tree
   - Parallel git operations controlled by `concurrency` (default: 1)
   - No rate limiting (disk I/O bound, not API bound)

**Example:**
```bash
# Use 5 parallel API calls to build tree, then 10 parallel git operations
gitlabber --api-concurrency 5 --concurrency 10 /path/to/dest
```

**Why different defaults?**
- `api_concurrency=5`: Conservative default to respect API rate limits
- `concurrency=1`: Conservative default to avoid overwhelming disk I/O

**Tuning recommendations:**
- **API concurrency**: 5-10 for GitLab.com, 10-20 for self-hosted (if rate limits allow)
- **Git concurrency**: 1-5 for HDD, 5-20 for SSD, depends on network bandwidth

## Error Handling

### Rate Limit Errors (429)

**Strategy:**
- Exponential backoff with jitter
- Retry after `Retry-After` header
- Log warning, continue with reduced concurrency

### Network Errors

**Strategy:**
- Retry with exponential backoff
- Fail individual group, continue with others
- Respect `fail_fast` setting

## Testing Considerations

### Unit Tests
- Mock rate limiter
- Test parallel execution
- Test error handling

### Integration Tests
- Test with mock GitLab API
- Verify rate limit compliance
- Test concurrent access

### E2E Tests
- Test with real GitLab instance
- Verify performance improvement
- Monitor rate limit headers

## Conclusion

**Parallel API calls efficiency: ⭐⭐⭐⭐⭐ (Very High)**

This is a **high-value optimization** that will provide significant performance improvements, especially for:
- Large GitLab instances
- Deep group hierarchies
- Many groups with many projects

**Recommended approach:**
1. **Start with Phase 1** (parallel group processing) - High impact, low risk
2. **Add simple rate limiter** - Prevents API abuse
3. **Measure performance** - Verify improvements
4. **Consider Phase 2** - If needed for very large instances

**Complexity is manageable** with proper rate limiting and error handling.

