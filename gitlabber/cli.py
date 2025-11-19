"""Command-line interface for gitlabber.

This module provides the CLI interface using Typer, handling argument
parsing, validation, and orchestrating the main application flow.
It supports configuration via command-line arguments, environment
variables, and configuration files.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Optional

import typer

from . import __version__ as VERSION
from .archive import ArchivedResults
from .auth import TokenAuthProvider
from .config import GitlabberConfig, GitlabberSettings
from .format import PrintFormat
from .gitlab_tree import GitlabTree
from .method import CloneMethod
from .naming import FolderNaming
from .token_storage import TokenStorage, TokenStorageError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)

app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _validate_positive_int(value: int) -> int:
    if value <= 0:
        raise typer.BadParameter("Value must be a positive integer")
    return value


def _validate_url(value: str) -> str:
    from urllib.parse import urlparse

    if not value or not value.strip():
        raise typer.BadParameter("URL cannot be empty")

    parsed = urlparse(value.strip())
    if not parsed.scheme or not parsed.netloc:
        raise typer.BadParameter(
            "URL must include scheme (http:// or https://) and hostname"
        )

    if parsed.scheme not in ("http", "https"):
        raise typer.BadParameter("Scheme must be http:// or https://")

    return value.strip()


def _convert_archived(value: str) -> ArchivedResults:
    """Convert string to ArchivedResults enum.
    
    Args:
        value: String value (case-insensitive): 'include', 'exclude', or 'only'
        
    Returns:
        ArchivedResults enum value
        
    Raises:
        typer.BadParameter: If value is not a valid enum name
    """
    if not isinstance(value, str):
        return value
    value_lower = value.lower()
    for enum_value in ArchivedResults:
        if enum_value.name.lower() == value_lower:
            return enum_value
    raise typer.BadParameter(
        f"'{value}' is not a valid value. Choose from: {', '.join(e.name.lower() for e in ArchivedResults)}"
    )


def _normalize_path(value: Optional[str]) -> Optional[str]:
    if value and value.endswith("/"):
        return value[:-1]
    return value


def _split_csv(csv: Optional[str]) -> Optional[list[str]]:
    if not csv or not csv.strip():
        return None
    values = [item.strip() for item in csv.split(",") if item.strip()]
    return values or None


def config_logging(verbose: bool, print_mode: bool) -> None:
    if verbose:
        handler = logging.StreamHandler()
        logging.root.handlers = []
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )
        logging.root.addHandler(handler)
        level = logging.ERROR if print_mode else logging.DEBUG
        logging.root.setLevel(level)
        log.debug(
            "verbose=[%s], print=[%s], log level set to [%s] level",
            verbose,
            print_mode,
            level,
        )
        os.environ["GIT_PYTHON_TRACE"] = "full"
    else:
        logging.getLogger().setLevel(logging.INFO)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(VERSION)
        sys.exit(0)


def _require(value: Optional[str], message: str) -> str:
    if not value:
        from .exceptions import format_error_with_suggestion
        error_msg, suggestion = format_error_with_suggestion(
            'config_missing',
            message,
            {}
        )
        typer.secho(error_msg, err=True)
        if suggestion:
            typer.secho(f"\n💡 Suggestion: {suggestion}", err=True)
        raise typer.Exit(1)
    return value


def _resolve_token(
    cli_token: Optional[str],
    url: str,
    settings: GitlabberSettings,
) -> str:
    """Resolve token from various sources in priority order.
    
    Priority:
    1. CLI argument (-t/--token) - highest priority
    2. Stored token (from secure storage)
    3. Environment variable (GITLAB_TOKEN) - from settings
    
    Args:
        cli_token: Token from CLI argument
        url: GitLab instance URL
        settings: Settings loaded from environment variables
        
    Returns:
        Resolved token string
        
    Raises:
        typer.Exit: If no token found
    """
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
    if settings.token:
        return settings.token
    
    # 4. Error - no token found
    from .exceptions import format_error_with_suggestion
    error_msg, suggestion = format_error_with_suggestion(
        'config_missing',
        "Please specify a valid token with -t/--token or the GITLAB_TOKEN environment variable.",
        {}
    )
    typer.secho(error_msg, err=True)
    if suggestion:
        typer.secho(f"\n💡 {suggestion}", err=True)
    raise typer.Exit(1)


def run_gitlabber(
    *,
    dest: Optional[str],
    token: Optional[str],
    hide_token: bool,
    url: Optional[str],
    verbose: bool,
    file: Optional[str],
    concurrency: Optional[int],
    api_concurrency: Optional[int],
    print_tree_only: bool,
    print_format: PrintFormat,
    naming: FolderNaming,
    method: CloneMethod,
    archived: ArchivedResults,
    include: Optional[str],
    exclude: Optional[str],
    recursive: bool,
    use_fetch: bool,
    include_shared: bool,
    group_search: Optional[str],
    user_projects: bool,
    git_options: Optional[str],
    fail_fast: bool,
    settings: GitlabberSettings,
) -> None:
    """Execute the main gitlabber workflow.
    
    This function orchestrates the complete gitlabber workflow:
    - Validates required parameters (token, URL)
    - Creates configuration from CLI args and environment settings
    - Builds the GitLab project tree
    - Either prints the tree or synchronizes repositories
    
    Args:
        dest: Destination directory for cloned repositories
        token: GitLab personal access token
        hide_token: Whether to hide token in repository URLs
        url: GitLab instance base URL
        verbose: Enable verbose logging
        file: Optional YAML file to load tree from
        concurrency: Number of concurrent git operations
        api_concurrency: Number of concurrent API calls
        print_tree_only: If True, only print tree without cloning
        print_format: Format for tree output (JSON, YAML, or TREE)
        naming: Folder naming strategy (NAME or PATH)
        method: Clone method (SSH or HTTP)
        archived: How to handle archived projects
        include: Comma-separated glob patterns to include
        exclude: Comma-separated glob patterns to exclude
        recursive: Clone submodules recursively
        use_fetch: Use git fetch instead of pull
        include_shared: Include shared projects
        group_search: Search term for filtering groups at API level
        user_projects: Fetch only user personal projects
        git_options: Additional git options as comma-separated string
        fail_fast: Exit immediately on discovery errors
        settings: Settings loaded from environment variables
        
    Raises:
        typer.Exit: If required parameters are missing or tree is empty
    """
    url_value = _require(
        url or settings.url,
        "Please specify a valid gitlab base url with -u/--url or the GITLAB_URL environment variable.",
    )
    
    # Resolve token with priority: CLI -> Stored -> Env var
    token_value = _resolve_token(token, url_value, settings)
    if not print_tree_only and dest is None and not user_projects:
        typer.secho(
            "Please specify a destination for the gitlab tree.",
            err=True,
        )
        raise typer.Exit(1)

    method_value = method or settings.method or CloneMethod.SSH
    naming_value = naming or settings.naming or FolderNaming.NAME
    includes_value = _split_csv(include)
    if includes_value is None:
        includes_value = settings.includes
    excludes_value = _split_csv(exclude)
    if excludes_value is None:
        excludes_value = settings.excludes
    concurrency_value = concurrency or settings.concurrency or 1
    api_concurrency_value = api_concurrency or settings.api_concurrency or 5

    config_logging(verbose, print_tree_only)

    log.debug(
        "running with args [%s]",
        {
            "dest": dest,
            "url": url_value,
            "token": "__hidden__",
            "print": print_tree_only,
            "print_format": print_format,
            "method": method_value,
            "naming": naming_value,
            "archived": archived,
            "recursive": recursive,
            "include_shared": include_shared,
            "use_fetch": use_fetch,
            "hide_token": hide_token,
            "user_projects": user_projects,
            "group_search": group_search,
            "fail_fast": fail_fast,
        },
    )

    auth_provider = TokenAuthProvider(token_value)
    config = GitlabberConfig(
        url=url_value,
        token=token_value,
        method=method_value,
        naming=naming_value,
        archived=archived.api_value,
        includes=includes_value,
        excludes=excludes_value,
        in_file=file,
        concurrency=concurrency_value,
        api_concurrency=api_concurrency_value,
        recursive=recursive,
        disable_progress=verbose,
        include_shared=include_shared,
        use_fetch=use_fetch,
        hide_token=hide_token,
        user_projects=user_projects,
        group_search=group_search,
        git_options=git_options,
        auth_provider=auth_provider,
        fail_fast=fail_fast,
    )

    tree = GitlabTree(config=config)
    tree.load_tree()

    if print_tree_only:
        # In print mode, allow empty trees to be printed (user might want to see empty result)
        tree.print_tree(print_format)
    else:
        # In sync mode, empty tree is an error
        if tree.is_empty():
            from .exceptions import format_error_with_suggestion
            error_msg, suggestion = format_error_with_suggestion(
                'tree_empty',
                "The tree is empty - no projects found matching your criteria.",
                {}
            )
            log.critical(error_msg)
            raise typer.Exit(1)
        tree.sync_tree(dest or ".")


@app.command()
def cli(
    dest: Optional[str] = typer.Argument(
        None,
        callback=_normalize_path,
        help="Destination path for the cloned tree (created if it doesn't exist)",
    ),
    token: Optional[str] = typer.Option(
        None,
        "-t",
        "--token",
        help="GitLab personal access token",
    ),
    hide_token: bool = typer.Option(
        False,
        "-T",
        "--hide-token",
        help="Use inline URL token (avoids storing the token in .git/config)",
    ),
    url: Optional[str] = typer.Option(
        None,
        "-u",
        "--url",
        callback=lambda value: _validate_url(value) if value else value,
        help="Base GitLab URL (e.g. https://gitlab.example.com)",
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        help="Print more verbose output",
    ),
    file: Optional[str] = typer.Option(
        None,
        "-f",
        "--file",
        help="Load tree definition from YAML file instead of querying GitLab",
        show_default=False,
    ),
    concurrency: Optional[int] = typer.Option(
        None,
        "-c",
        "--concurrency",
        callback=lambda v: _validate_positive_int(v) if v is not None else v,
        help="Number of concurrent git operations",
    ),
    api_concurrency: Optional[int] = typer.Option(
        None,
        "--api-concurrency",
        callback=lambda v: _validate_positive_int(v) if v is not None else v,
        help="Number of concurrent API calls (default: 5)",
    ),
    print_tree_only: bool = typer.Option(
        False,
        "-p",
        "--print",
        help="Print the tree without cloning",
    ),
    print_format: PrintFormat = typer.Option(
        PrintFormat.TREE,
        "--print-format",
        case_sensitive=False,
        help="Print format",
    ),
    fail_fast: bool = typer.Option(
        False,
        "--fail-fast",
        help="Exit immediately when encountering discovery errors",
    ),
    naming: Optional[FolderNaming] = typer.Option(
        None,
        "-n",
        "--naming",
        case_sensitive=False,
        help="Folder naming strategy for projects",
    ),
    method: Optional[CloneMethod] = typer.Option(
        None,
        "-m",
        "--method",
        case_sensitive=False,
        help="Git transport method to use for cloning",
    ),
    archived: str = typer.Option(
        "include",
        "-a",
        "--archived",
        case_sensitive=False,
        callback=_convert_archived,
        help="Include archived projects and groups in the results (options: include, exclude, only)",
    ),
    include: Optional[str] = typer.Option(
        None,
        "-i",
        "--include",
        help="Comma-delimited list of glob patterns to include",
    ),
    exclude: Optional[str] = typer.Option(
        None,
        "-x",
        "--exclude",
        help="Comma-delimited list of glob patterns to exclude",
    ),
    recursive: bool = typer.Option(
        False,
        "-r",
        "--recursive",
        help="Clone/pull git submodules recursively",
    ),
    use_fetch: bool = typer.Option(
        False,
        "-F",
        "--use-fetch",
        help="Use git fetch instead of pull (mirrored repositories)",
    ),
    exclude_shared: bool = typer.Option(
        False,
        "--exclude-shared",
        help="Exclude shared projects from the results",
    ),
    group_search: Optional[str] = typer.Option(
        None,
        "-g",
        "--group-search",
        help="Only include groups matching the search term (API level filtering)",
    ),
    user_projects: bool = typer.Option(
        False,
        "-U",
        "--user-projects",
        help="Fetch only user personal projects (group parameters ignored)",
    ),
    git_options: Optional[str] = typer.Option(
        None,
        "-o",
        "--git-options",
        help="Additional options as CSV for the git command (e.g., --depth=1)",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Print version and exit",
    ),
    store_token: bool = typer.Option(
        False,
        "--store-token",
        help="Store token securely in OS keyring (requires keyring package)",
    ),
) -> None:
    """Main CLI command for gitlabber.
    
    This command provides the command-line interface for gitlabber,
    accepting all configuration options via command-line arguments.
    Options can also be provided via environment variables (see GitlabberSettings).
    """
    # Early exit for version - don't instantiate settings or run main logic
    # This is a safety check in case the callback doesn't prevent execution
    if version:
        typer.echo(VERSION)
        sys.exit(0)
    
    settings = GitlabberSettings()
    
    # Handle token storage
    if store_token:
        url_value = url or settings.url
        if not url_value:
            typer.secho(
                "Error: URL required for storing token. Use -u/--url or GITLAB_URL.",
                err=True,
            )
            raise typer.Exit(1)
        
        # Get token from CLI or prompt
        token_to_store = token
        if not token_to_store:
            token_to_store = typer.prompt("Enter token", hide_input=True)
        
        try:
            storage = TokenStorage()
            if not storage.is_available():
                typer.secho(
                    "Error: keyring not available. Install with: pip install keyring",
                    err=True,
                )
                raise typer.Exit(1)
            storage.store(url_value, token_to_store)
            typer.echo(f"Token stored securely in keyring for {url_value} ✓")
        except TokenStorageError as e:
            typer.secho(f"Error: {str(e)}", err=True)
            raise typer.Exit(1)
        raise typer.Exit(0)  # Exit after storing
    
    include_shared_value = not exclude_shared

    run_gitlabber(
        dest=dest,
        token=token,
        hide_token=hide_token,
        url=url,
        verbose=verbose,
        file=file,
        concurrency=concurrency,
        api_concurrency=api_concurrency,
        print_tree_only=print_tree_only,
        print_format=print_format,
        naming=naming,
        method=method,
        archived=archived,
        include=include,
        exclude=exclude,
        recursive=recursive,
        use_fetch=use_fetch,
        include_shared=include_shared_value,
        group_search=group_search,
        user_projects=user_projects,
        git_options=git_options,
        fail_fast=fail_fast,
        settings=settings,
    )


def main() -> None:
    """Entry point for the gitlabber CLI application.
    
    This function is called when gitlabber is executed as a script
    or module. It invokes the Typer application.
    """
    app()

