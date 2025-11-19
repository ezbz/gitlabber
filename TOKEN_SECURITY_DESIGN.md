# Token Security Features Design (Simplified)

## Overview

This document outlines a **simplified** design for basic secure token storage in gitlabber. Token rotation and validation are considered out of scope - users can manage these themselves.

## Current State

- Tokens are passed via CLI (`-t/--token`) or environment variables (`GITLAB_TOKEN`)
- Tokens are stored in plain text in memory
- No secure storage mechanism

## Design Philosophy

**Keep it simple**: gitlabber is a utility tool. Users can:
- Manage token rotation themselves (revoke old, create new in GitLab)
- Validate tokens themselves (if token fails, they'll know)
- Use environment variables or password managers for token management

**What we add**: Just basic secure storage as a convenience feature.

---

## Simplified Design: Basic Secure Storage Only

### 1. Single Storage Backend: OS Keyring

Use the `keyring` library for OS-native secure storage:
- **macOS**: Keychain
- **Linux**: Secret Service API (GNOME Keyring, KWallet)
- **Windows**: Windows Credential Manager

**Why only keyring?**
- Most secure option
- OS-managed, no password prompts needed
- Simple implementation
- If keyring unavailable, fall back to current behavior (env var/CLI)

### 2. Minimal Implementation

```python
# gitlabber/token_storage.py

from typing import Optional

class TokenStorage:
    """Simple token storage using OS keyring."""
    
    SERVICE_NAME = "gitlabber"
    
    def __init__(self):
        self._keyring = None
        self._try_import_keyring()
    
    def _try_import_keyring(self):
        """Try to import keyring, fail silently if unavailable."""
        try:
            import keyring
            self._keyring = keyring
        except ImportError:
            self._keyring = None
    
    def is_available(self) -> bool:
        """Check if keyring storage is available."""
        return self._keyring is not None
    
    def store(self, url: str, token: str) -> None:
        """Store token for a GitLab URL."""
        if not self.is_available():
            raise TokenStorageError("Keyring not available. Install with: pip install keyring")
        self._keyring.set_password(self.SERVICE_NAME, url, token)
    
    def retrieve(self, url: str) -> Optional[str]:
        """Retrieve token for a GitLab URL."""
        if not self.is_available():
            return None
        return self._keyring.get_password(self.SERVICE_NAME, url)
    
    def delete(self, url: str) -> None:
        """Delete stored token for a GitLab URL."""
        if not self.is_available():
            return
        try:
            self._keyring.delete_password(self.SERVICE_NAME, url)
        except Exception:
            pass  # Ignore if not found
```

### 3. Simple CLI Integration

```python
# New CLI options (minimal):
--store-token          # Store token in keyring (requires keyring package)
--use-stored-token     # Use stored token instead of CLI/env (optional flag)

# Token resolution (automatic, no flags needed):
1. CLI argument (-t/--token) - highest priority
2. Stored token (if --use-stored-token or no CLI token provided)
3. Environment variable (GITLAB_TOKEN) - current behavior
```

### 4. Usage Examples

```bash
# Store token (one-time setup)
$ pip install keyring  # Optional dependency
$ gitlabber --store-token -u https://gitlab.com
Enter token: [hidden]
Token stored in keyring ✓

# Use stored token automatically
$ gitlabber -u https://gitlab.com .
# Automatically uses stored token if no -t flag provided

# Override with CLI token
$ gitlabber -t <token> -u https://gitlab.com .
# Uses CLI token (highest priority)

# Delete stored token
$ gitlabber token delete https://gitlab.com
```

### 5. Implementation Details

#### Token Resolution Flow

```python
def resolve_token(cli_token: Optional[str], url: str) -> str:
    """Resolve token from various sources."""
    # 1. CLI token (highest priority)
    if cli_token:
        return cli_token
    
    # 2. Stored token (if available)
    storage = TokenStorage()
    if storage.is_available():
        stored = storage.retrieve(url)
        if stored:
            return stored
    
    # 3. Environment variable (current behavior)
    env_token = os.environ.get("GITLAB_TOKEN")
    if env_token:
        return env_token
    
    # 4. Error - no token found
    raise TokenNotFoundError("No token provided")
```

#### CLI Changes

```python
# Minimal additions to cli.py

store_token: bool = typer.Option(
    False,
    "--store-token",
    help="Store token securely in OS keyring (requires keyring package)",
)

# In cli() function:
if store_token:
    if not token:
        token = typer.prompt("Enter token", hide_input=True)
    storage = TokenStorage()
    if not storage.is_available():
        typer.echo("Error: keyring not available. Install with: pip install keyring", err=True)
        raise typer.Exit(1)
    storage.store(url or settings.url or "default", token)
    typer.echo("Token stored securely ✓")
    return  # Exit after storing
```

### 6. Dependencies

```python
# pyproject.toml
[project.optional-dependencies]
keyring = ["keyring>=24.0.0"]

# Installation
pip install gitlabber[keyring]  # Optional
```

### 7. What We DON'T Implement

**Token Rotation**: Users manage this themselves
- Revoke old token in GitLab UI
- Create new token
- Store new token: `gitlabber --store-token -t <new-token> -u <url>`

**Token Validation**: Not needed
- If token is invalid, GitLab API will return 401
- User gets clear error message
- No need for pre-validation

**Encrypted File Backend**: Too complex
- Requires password prompts
- Adds cryptography dependency
- Keyring is sufficient for most users
- If keyring unavailable, use env vars (current behavior)

**Fallback Tokens**: Overkill
- Users can manage multiple tokens themselves
- Adds unnecessary complexity

### 8. Benefits of Simplified Approach

✅ **Simple**: One storage backend, minimal code
✅ **Secure**: OS-managed keyring encryption
✅ **Optional**: Works without keyring (current behavior)
✅ **No Breaking Changes**: All existing workflows continue to work
✅ **User Control**: Users manage token lifecycle themselves

### 9. Migration Path

- **Zero migration needed**: Existing workflows unchanged
- **Opt-in**: Users choose to use `--store-token` if they want
- **Backward compatible**: Env vars and CLI args work as before

### 10. Testing

- Test keyring storage/retrieval
- Test fallback to env var when keyring unavailable
- Test CLI token priority over stored token
- Test error handling when keyring not installed

---

## Conclusion

This simplified design provides basic secure storage without the complexity of rotation, validation, or multiple backends. Users retain full control over token management, and the feature is completely optional.

**Estimated Implementation**: ~200 lines of code vs. ~1000+ for full design.
