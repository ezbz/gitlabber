# Contributing to Gitlabber

Thank you for your interest in contributing to Gitlabber! This document provides guidelines and instructions for contributing.

## Code of Conduct

Please note we have a [Code of Conduct](CODE_OF_CONDUCT.md). Please follow it in all your interactions with the project.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git 2.0 or higher
- pip

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/ezbz/gitlabber.git
   cd gitlabber
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -e ".[test]"
   ```

   This installs the package in editable mode with all test dependencies.

4. **Verify installation:**
   ```bash
   gitlabber --version
   pytest --version
   ```

## Development Workflow

1. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes:**
   - Follow the code style guidelines (see below)
   - Write or update tests
   - Update documentation as needed

3. **Run tests:**
   ```bash
   pytest
   ```

4. **Check code quality:**
   ```bash
   # Run linters (if configured)
   ruff check .
   mypy gitlabber/
   ```

5. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test changes
   - `refactor:` for code refactoring
   - `chore:` for maintenance tasks

6. **Push and create a Pull Request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## Code Style

- **Python Version:** Python 3.11+ (use modern Python features)
- **Type Hints:** Use type hints for all function signatures
- **Docstrings:** Follow Google-style docstrings for all public APIs
- **Formatting:** Code should be formatted with `black` (if configured)
- **Imports:** Use absolute imports, group by standard library, third-party, local
- **Naming:**
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gitlabber --cov-report=html

# Run specific test file
pytest tests/test_git.py

# Run with verbose output
pytest -v

# Run only fast tests (skip integration tests)
pytest -m "not integration_test"
```

### Writing Tests

- Place tests in the `tests/` directory
- Test files should be named `test_*.py`
- Use descriptive test function names: `test_<what>_<condition>_<expected_result>`
- Use fixtures from `conftest.py` for common test setup
- Use test helpers from `tests/test_helpers.py` for reusable utilities
- Mock external dependencies (GitLab API, Git operations)
- Aim for high test coverage (>90%)

### Test Structure

```python
def test_function_name_condition_expected():
    """Test description."""
    # Arrange
    # Act
    # Assert
```

## Pull Request Process

1. **Before submitting:**
   - Ensure all tests pass
   - Update documentation if needed
   - Add changelog entry if applicable
   - Ensure code follows style guidelines

2. **PR Description:**
   - Clearly describe what changes were made
   - Explain why the changes were needed
   - Reference any related issues
   - Include screenshots if UI changes

3. **Review process:**
   - Maintainers will review your PR
   - Address any feedback or requested changes
   - Keep PRs focused and reasonably sized

## Building and Releasing

### Building

```bash
pip install build
python -m build
```

This creates distribution packages in the `dist/` directory.

### Testing Distribution

```bash
# Check the built package
twine check dist/*

# Test installation
pip install dist/gitlabber-*.whl
```

### Release Process

Releases are handled by maintainers. The process includes:
1. Update version in `pyproject.toml` and `gitlabber/__init__.py`
2. Update `CHANGELOG.md`
3. Create a git tag
4. Build and upload to PyPI

## Getting Help

- **Issues:** Open an issue for bugs or feature requests
- **Discussions:** Use GitHub Discussions for questions
- **Email:** Contact maintainers via email if needed

## Dependencies

### Runtime Dependencies

See `pyproject.toml` for the complete list. Main dependencies:
- `anytree` - Tree data structure
- `globre` - Glob pattern matching
- `pyyaml` - YAML parsing
- `pydantic` - Configuration validation
- `typer` - CLI framework
- `rich` - Progress bars and formatting
- `GitPython` - Git operations
- `python-gitlab` - GitLab API client

### Development Dependencies

- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `pytest-integration` - Integration test support
- `coverage` - Code coverage analysis

## Questions?

If you have questions about contributing, feel free to:
- Open an issue
- Start a discussion
- Contact the maintainers

Thank you for contributing to Gitlabber!
