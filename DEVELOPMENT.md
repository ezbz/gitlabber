# Development Guide

This document provides an overview of the Gitlabber codebase architecture, project structure, and development practices.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Module Descriptions](#module-descriptions)
- [Key Design Decisions](#key-design-decisions)
- [Development Workflow](#development-workflow)
- [Debugging](#debugging)

## Architecture Overview

Gitlabber follows a modular architecture with clear separation of concerns:

```
┌─────────────┐
│     CLI     │  (cli.py) - User interface, argument parsing
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Config    │  (config.py) - Configuration management
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ GitlabTree  │  (gitlab_tree.py) - Main orchestrator
└──────┬──────┘
       │
       ├──────────────┬──────────────┐
       ▼              ▼              ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│Tree Builder │ │Tree Filter  │ │   Git Ops   │
│(tree_builder│ │(tree_builder│ │   (git.py)  │
│    .py)     │ │    .py)     │ │             │
└─────────────┘ └─────────────┘ └─────────────┘
```

### Data Flow

1. **CLI Layer** (`cli.py`): Parses arguments, validates input, loads settings
2. **Configuration Layer** (`config.py`): Validates and merges config from CLI, env vars, and files
3. **Tree Management** (`gitlab_tree.py`): Orchestrates tree building, filtering, and syncing
4. **Tree Building** (`tree_builder.py`): Fetches data from GitLab API and builds tree structure
5. **Tree Filtering** (`tree_builder.py`): Applies include/exclude patterns using functional approach
6. **Git Operations** (`git.py`): Handles cloning, pulling, and syncing repositories

## Project Structure

```
gitlabber/
├── gitlabber/              # Main package
│   ├── __init__.py         # Package initialization
│   ├── __main__.py         # Entry point for `python -m gitlabber`
│   ├── cli.py              # Command-line interface (Typer)
│   ├── config.py           # Configuration classes (Pydantic)
│   ├── gitlab_tree.py      # Main tree orchestrator
│   ├── tree_builder.py     # Tree building and filtering
│   ├── git.py              # Git operations
│   ├── url_builder.py      # URL construction utilities
│   ├── progress.py         # Progress reporting (Rich)
│   ├── auth.py             # Authentication providers
│   ├── exceptions.py       # Custom exception hierarchy
│   ├── archive.py          # Archive handling enum
│   ├── format.py           # Output format enum
│   ├── method.py           # Clone method enum
│   └── naming.py           # Folder naming enum
│
├── tests/                  # Test suite
│   ├── conftest.py         # Pytest fixtures
│   ├── test_helpers.py     # Test utilities
│   ├── test_*.py           # Unit tests
│   └── ...
│
├── docs/                   # Documentation
├── pyproject.toml          # Project configuration
├── README.md               # User documentation
├── CONTRIBUTING.md         # Contribution guidelines
└── DEVELOPMENT.md          # This file
```

## Module Descriptions

### Core Modules

#### `cli.py`
- **Purpose:** Command-line interface using Typer
- **Key Classes/Functions:**
  - `cli()`: Main CLI command
  - `run_gitlabber()`: Orchestrates the main workflow
  - `main()`: Entry point
- **Dependencies:** Typer, Rich

#### `config.py`
- **Purpose:** Configuration management with validation
- **Key Classes:**
  - `GitlabberSettings`: Loads from environment variables (Pydantic Settings)
  - `GitlabberConfig`: Validated configuration (Pydantic Model)
- **Dependencies:** Pydantic, Pydantic Settings

#### `gitlab_tree.py`
- **Purpose:** Main orchestrator for tree operations
- **Key Classes:**
  - `GitlabTree`: Main class that coordinates tree building, filtering, printing, and syncing
- **Responsibilities:**
  - Initializes GitLab client
  - Delegates to `GitlabTreeBuilder` for tree construction
  - Delegates to `TreeFilter` for filtering
  - Handles tree printing in various formats
  - Coordinates repository synchronization

#### `tree_builder.py`
- **Purpose:** Tree building and filtering logic
- **Key Classes:**
  - `GitlabTreeBuilder`: Builds tree from GitLab API or YAML file
  - `TreeFilter`: Filters tree using functional predicates
- **Key Functions:**
  - `create_pattern_matcher()`: Creates glob pattern matcher
  - `create_include_predicate()`: Creates include filter
  - `create_exclude_predicate()`: Creates exclude filter
  - `filter_tree_functional()`: Functional tree filtering
- **Design:** Uses functional programming approach for filtering

#### `git.py`
- **Purpose:** Git repository operations
- **Key Classes:**
  - `GitAction`: Dataclass describing a git operation
  - `GitRepository`: Static methods for git operations (clone, pull)
  - `GitActionCollector`: Collects git actions from tree
  - `GitSyncManager`: Manages concurrent git operations
- **Key Functions:**
  - `sync_tree()`: Main entry point for syncing (backward compatibility)
  - `clone_or_pull_project()`: Execute a single git action
- **Dependencies:** GitPython, concurrent.futures

#### `url_builder.py`
- **Purpose:** URL construction for repository cloning
- **Key Functions:**
  - `select_project_url()`: Selects HTTP or SSH URL based on method
  - `build_project_url()`: Builds final URL with optional token injection
- **Design:** Pure functions, no state

#### `progress.py`
- **Purpose:** Progress reporting during operations
- **Key Classes:**
  - `ProgressBar`: Main progress bar manager
  - `ProgressTaskHandle`: Context manager for individual tasks
- **Features:**
  - Multiple concurrent progress bars
  - Context manager support
  - Rich library integration
- **Dependencies:** Rich

#### `auth.py`
- **Purpose:** Authentication providers for GitLab API
- **Key Classes:**
  - `AuthProvider`: Abstract base class
  - `TokenAuthProvider`: Token-based authentication
  - `NoAuthProvider`: No-op provider for testing
- **Design:** Strategy pattern

### Supporting Modules

#### `exceptions.py`
- Custom exception hierarchy:
  - `GitlabberError`: Base exception
  - `GitlabberConfigError`: Configuration errors
  - `GitlabberAPIError`: GitLab API errors
  - `GitlabberAuthenticationError`: Authentication errors
  - `GitlabberGitError`: Git operation errors
  - `GitlabberTreeError`: Tree operation errors

#### Enum Modules
- `archive.py`: `ArchivedResults` - How to handle archived projects
- `format.py`: `PrintFormat` - Output format (JSON, YAML, TREE)
- `method.py`: `CloneMethod` - Clone method (SSH, HTTP)
- `naming.py`: `FolderNaming` - Folder naming strategy (NAME, PATH)

## Key Design Decisions

### 1. Separation of Concerns

The codebase has been refactored to separate concerns:
- **Tree Building** (`GitlabTreeBuilder`): Handles API interactions and tree construction
- **Tree Filtering** (`TreeFilter`): Handles filtering logic using functional approach
- **Git Operations** (`GitRepository`, `GitSyncManager`): Handles all git operations
- **URL Building** (`url_builder.py`): Centralized URL construction

### 2. Functional Filtering

Tree filtering uses a functional programming approach:
- Pure functions for pattern matching
- Composable predicates
- Immutable tree operations
- Easier to test and reason about

### 3. Configuration Management

- Uses Pydantic for validation
- Supports multiple sources: CLI args, environment variables, config files
- Type-safe configuration objects
- Clear validation errors

### 4. Progress Reporting

- Context manager pattern for resource management
- Support for multiple concurrent progress bars
- Rich library for better UX
- Can be disabled for scripting/CI

### 5. Error Handling

- Custom exception hierarchy for better error context
- Specific exceptions for different error types
- Proper error propagation and logging

### 6. Concurrency

- Uses `ThreadPoolExecutor` for concurrent git operations
- Configurable concurrency level
- Thread-safe progress reporting

## Development Workflow

### 1. Setting Up Development Environment

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed setup instructions.

### 2. Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make your changes:**
   - Follow the architecture patterns
   - Add/update tests
   - Update documentation

3. **Test your changes:**
   ```bash
   pytest
   pytest --cov=gitlabber
   ```

4. **Run linting:**
   ```bash
   ruff check .
   mypy gitlabber/
   ```

### 3. Testing Strategy

- **Unit Tests:** Test individual functions/classes in isolation
- **Integration Tests:** Test component interactions
- **E2E Tests:** Test full workflows (marked with `@pytest.mark.slow_integration_test`)

#### Running E2E Tests

E2E tests are marked with `@pytest.mark.slow_integration_test` and are **skipped by default** to avoid long-running tests during development. These tests require:

1. **GitLab Token:** Set `GITLAB_TOKEN` environment variable with a valid GitLab personal access token
2. **GitLab URL:** Set `GITLAB_URL` environment variable (defaults to `https://gitlab.com/`)
3. **Test Data:** Access to specific test groups/projects on GitLab.com (these are private test repositories)

**To run E2E tests:**

```bash
# Run all e2e tests
pytest tests/test_e2e.py -m slow_integration_test --with-slow-integration

# Run a specific e2e test
pytest tests/test_e2e.py::test_clone_subgroup -m slow_integration_test --with-slow-integration

# With environment variables
GITLAB_TOKEN=your_token GITLAB_URL=https://gitlab.com/ pytest tests/test_e2e.py -m slow_integration_test --with-slow-integration
```

**Note:** E2E tests use `--verbose` flag to disable progress bars, ensuring clean JSON output for parsing.

**E2E Test Files:**
- `tests/test_e2e.py`: Tests against real GitLab.com API with actual groups/projects
- `tests/test_integration.py`: Integration tests that don't require external API access

### 4. Code Review Checklist

- [ ] Code follows project architecture
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Type hints added
- [ ] Docstrings added for public APIs
- [ ] No linter errors
- [ ] All tests pass

## Debugging

### Enable Verbose Logging

```bash
gitlabber --verbose -t <token> -u <url> .
```

This enables:
- Debug-level logging
- GitPython trace output
- Detailed error messages

### Debugging in Code

1. **Add logging:**
   ```python
   import logging
   log = logging.getLogger(__name__)
   log.debug("Debug message: %s", variable)
   ```

2. **Use breakpoints:**
   ```python
   import pdb; pdb.set_trace()
   ```

3. **Test individual components:**
   ```python
   from gitlabber.tree_builder import GitlabTreeBuilder
   # Test tree building in isolation
   ```

### Common Issues

1. **GitLab API Errors:**
   - Check token permissions
   - Verify URL is correct
   - Check network connectivity
   - Enable verbose logging

2. **Git Operation Errors:**
   - Check Git is installed
   - Verify SSH keys (for SSH method)
   - Check disk space
   - Review git error messages

3. **Tree Building Issues:**
   - Verify include/exclude patterns
   - Check API permissions
   - Review tree structure with `--print`

### Testing with Mock Data

Use test utilities from `tests/test_helpers.py`:
- `MockGitRepo`: Mock git operations
- `MockGitlabAPI`: Mock GitLab API responses
- `TreeBuilder`: Build test trees
- `TestConfigBuilder`: Create test configurations

## Architecture Evolution

The codebase has evolved through several refactorings:

1. **Initial:** Monolithic `GitlabTree` class
2. **Refactored:** Separated tree building, filtering, and git operations
3. **Current:** Functional filtering, better separation of concerns, improved testability

Future improvements may include:
- Async API support
- Caching for API responses
- Plugin system for custom filters
- Better error recovery

## Additional Resources

- [README.md](README.md) - User documentation
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [CHANGELOG.md](CHANGELOG.md) - Version history
- [Code of Conduct](CODE_OF_CONDUCT.md) - Community guidelines

