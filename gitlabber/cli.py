from __future__ import annotations

import logging
import os
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
        raise typer.Exit()


def _require(value: Optional[str], message: str) -> str:
    if not value:
        typer.secho(message, err=True)
        raise typer.Exit(1)
    return value


def run_gitlabber(
    *,
    dest: Optional[str],
    token: Optional[str],
    hide_token: bool,
    url: Optional[str],
    verbose: bool,
    file: Optional[str],
    concurrency: Optional[int],
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
    token_value = _require(
        token or settings.token,
        "Please specify a valid token with -t/--token or the GITLAB_TOKEN environment variable.",
    )
    url_value = _require(
        url or settings.url,
        "Please specify a valid gitlab base url with -u/--url or the GITLAB_URL environment variable.",
    )
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

    if tree.is_empty():
        log.critical(
            "The tree is empty, check your include/exclude patterns or run with more verbosity for debugging",
        )
        raise typer.Exit(1)

    if print_tree_only:
        tree.print_tree(print_format)
    else:
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
    archived: ArchivedResults = typer.Option(
        ArchivedResults.INCLUDE,
        "-a",
        "--archived",
        case_sensitive=False,
        help="Include archived projects and groups in the results",
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
    include_shared: bool = typer.Option(
        True,
        "--include-shared/--no-include-shared",
        help="Include shared projects in the results",
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
) -> None:
    settings = GitlabberSettings()

    run_gitlabber(
        dest=dest,
        token=token,
        hide_token=hide_token,
        url=url,
        verbose=verbose,
        file=file,
        concurrency=concurrency,
        print_tree_only=print_tree_only,
        print_format=print_format,
        naming=naming,
        method=method,
        archived=archived,
        include=include,
        exclude=exclude,
        recursive=recursive,
        use_fetch=use_fetch,
        include_shared=include_shared,
        group_search=group_search,
        user_projects=user_projects,
        git_options=git_options,
        fail_fast=fail_fast,
        settings=settings,
    )


def main() -> None:
    app()

