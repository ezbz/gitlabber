# Changelog

<!--next-version-placeholder-->
## [Unreleased]

## [2.0.0] - 2025-11-18

### Added
- **Major Performance Feature**: Add `--api-concurrency` option for parallel API calls during tree building. This dramatically speeds up tree discovery for large GitLab instances with many groups and subgroups. Real-world performance improvements: **4-6x speedup** (e.g., 96s → 16-21s for instances with 21+ subgroups). The feature includes:
  - Parallel group processing at the top level
  - Parallel subgroup detail fetching (batch processing)
  - Parallel subgroups and projects fetching within each group
  - Automatic connection pool sizing to prevent urllib3 warnings
  - Thread-safe rate limiting to respect GitLab API limits
  - Configurable via `--api-concurrency N` (default: 5, range: 1-20) or `GITLABBER_API_CONCURRENCY` environment variable
  - Optional `--api-rate-limit` to set custom rate limits (default: 2000 requests/hour)
- **Enhanced Progress Reporting**: Progress bars now show estimated time remaining (ETA) and current operation details (cloning, pulling, fetching, processing)
- **Actionable Error Messages**: Error messages now include context-specific suggestions with actionable steps and links to documentation
- **Pydantic-based Configuration**: Configuration management with automatic validation and environment variable support
- **Environment Variable Support**: All configuration options can now be set via environment variables (e.g., `GITLABBER_API_CONCURRENCY`, `GITLABBER_TOKEN`)
- **Comprehensive Documentation**: Added module-level docstrings, API documentation, `DEVELOPMENT.md` with architecture docs, and enhanced `CONTRIBUTING.md`
- **Pre-commit Hooks**: Added pre-commit hooks with black, ruff, mypy, and isort for code quality
- **Test Utilities**: Added comprehensive test helpers and utilities for better test organization
- **Performance Tests**: Added performance benchmarks and e2e tests for API concurrency
- **Custom Exception Hierarchy**: Structured exception classes for better error handling

### Changed
- **BREAKING**: Require Python 3.11 or newer (dropped Python 3.9 and 3.10 support)
- **BREAKING**: Migrate CLI implementation from argparse to Typer for modern option parsing and help output
- **BREAKING**: Replace tqdm-based progress bars with Rich for improved CLI UX (different visual appearance)
- Convert CLI enums to `enum.StrEnum` for clearer string semantics
- Modernize type hints throughout codebase (`list[str]` instead of `List[str]`)
- Convert `GitAction` to `@dataclass` for better code clarity
- Use `pathlib.Path` consistently throughout codebase
- Refactor `GitlabTree` into smaller, focused components:
  - `GitlabTreeBuilder`: Builds tree structure
  - `TreeFilter`: Handles filtering logic (functional approach)
  - `UrlBuilder`: Centralized URL construction
- Extract git operations into separate classes:
  - `GitRepository`: Wraps git operations for a single repo
  - `GitActionCollector`: Collects git actions
  - `GitSyncManager`: Manages concurrent git operations
- Improve tree filtering with functional approach and predicate composition
- Enhance error handling with specific exceptions and better context
- Improve input validation with `urllib.parse` for URLs
- Update dependencies: anytree 2.13.0, GitPython 3.1.45, python-gitlab 7.0.0, PyYAML 6.0.3
- Automatically configure HTTP connection pool size based on `--api-concurrency` to prevent connection pool warnings
- Improve test coverage from 92% to 97%
- Standardize logging (use `log.critical()` instead of `log.fatal()`)
- Use f-strings consistently throughout codebase

### Removed
- Remove unused `typing` dependency (built-in since Python 3.5+)
- Remove unused `docopt` dependency
- Remove refactoring-related comments from codebase
- Remove unused enum argparse methods (handled by Typer)

### Fixed
- Fix error handling to provide actionable suggestions
- Fix progress reporting to show accurate ETA
- Fix connection pool warnings with dynamic sizing
- Fix test coverage gaps in error handling and edge cases


## [1.2.8] - 25/3/2025
### Added
- Add support for shared projects fetching
### Changed
### Deprecated
### Removed
### Fixed
### Security


## [1.2.7] - 26/1/2024
### Added
- Add support for Python 3.13
### Changed
- Update dependencies
### Deprecated
### Removed
- Support for Python 3.8 (python gitlab library dropped support for it)
### Fixed
### Security


## [1.2.6] - 02/07/2024
### Added
- Added ability to provide git options to the GitPython clone/update method to support things like shallow clone (e.g., --depth=1)
### Changed
### Deprecated
### Removed
### Fixed
### Security

## [1.2.5] - 02/07/2024
### Added
- Added ability to clone a user's personal projects
### Changed
### Deprecated
### Removed
### Fixed
### Security


## [1.2.4] - 02/07/2024
### Added
### Changed
- Fix archived parameter incorrectly passed to api - there's no support for archived subgroups in the groups.subgroups API
- Introduce new paramter group-search, only groups matching the search term will be fetched from the API - using an SQL full Like on the name or the path of the group (useful for large projects), see: https://docs.gitlab.com/ee/api/groups.html#search-for-group
- Fix showing elapsed time as None when progress bar is disabled (verbose mode)
- Fix args not printing in verbose mode
- Fix cloning of subgroups throws a git error, new type attributes on nodes ensures only projects are clone
### Deprecated
### Removed
### Fixed
### Security



## [1.2.3] - 01/07/2024
### Added
### Changed
- fix pypi documentation
### Deprecated
### Removed
### Fixed
### Security

## [1.2.2] - 01/07/2024
### Added
### Changed
- debug statements for inclusion
- get all for groups
### Deprecated
### Removed
### Fixed
### Security
- 
## [1.2.1] - 30/06/2024
### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security
- move to latest urllib3 release for security improvments

## [1.2.0] - 30/06/2024

### Added
- Support new GitPython API (iterator depracation, pagination support)
- Support for excluding shared projects
- Support for fetching repositories instead of cloning (--mirror)
- Support for omitting the token from the URL in HTTP mode
### Changed
- Update depedencies for GiyPython, Python-Gitlab and others
### Deprecated
### Removed
### Fixed
### Security


## [1.1.9] - 12/07/2021

### Added
### Changed
- Update depedencies
### Deprecated
### Removed
### Fixed
### Security
## [1.1.8]  - 24/03/2021

### Added
### Changed
 - Changelog standartization
### Deprecated
### Removed
### Fixed
 - Fix recursive flag
### Security


## [1.1.7]  - 15/03/2021

### Added
### Changed
 - Move to GH actions
### Deprecated
### Removed
### Fixed
### Security
## [1.1.6] - 11/03/2021

### Added
### Changed
- Update depedencies
### Deprecated
### Removed
### Fixed
### Security
## [1.1.4] - 10/03/2021
### Added
### Changed
### Deprecated
### Removed
### Fixed
- Fixes to naming strategy
### Security
## [1.1.3] - 08/03/2021
### Added
- Support git submodules

### Changed
### Deprecated
### Removed
### Fixed
### Security
## [1.1.2] - 22/02/2021
### Added
- Support different local folder naming strategy (project path/name)
- support CA bundles 

### Changed
### Deprecated
### Removed
### Fixed
### Security
## [1.1.1] - 01/05/2021
### Added
 - Added concurrency 

### Changed
### Deprecated
### Removed
### Fixed
- Fix for pattern matching filtering out parents with relevant children
- Fix Gitlab groups API change not returning subgroups
### Security
## [1.1.0] - - 11/05/2020
### Added
- Add support for HTTP clone via CLI argument or ENV variable
### Changed
### Deprecated
### Removed
### Fixed
### Security
 ## [1.0.9] - 10/04/2020
### Added

- Documentation Changes
### Changed
### Deprecated
### Removed
### Fixed
### Security
 ## [1.0.8] - 28/03/2020
### Added

- First published version on PyPi
### Changed
### Deprecated
### Removed
### Fixed
### Security

[unreleased]: https://github.com/ezbz/gitlabber/compare/v2.0.1...HEAD
[2.0.1]: https://github.com/ezbz/gitlabber/compare/v2.0.0...v2.0.1
[2.0.0]: https://github.com/ezbz/gitlabber/compare/v1.2.8...v2.0.0
[1.2.8]: https://github.com/ezbz/gitlabber/compare/v1.2.7...v1.2.8
[1.2.7]: https://github.com/ezbz/gitlabber/compare/v1.2.6...v1.2.7
[1.2.6]: https://github.com/ezbz/gitlabber/compare/v1.2.5...v1.2.6
[1.2.5]: https://github.com/ezbz/gitlabber/compare/v1.2.4...v1.2.5
[1.2.4]: https://github.com/ezbz/gitlabber/compare/v1.2.3...v1.2.4
[1.2.3]: https://github.com/ezbz/gitlabber/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/ezbz/gitlabber/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/ezbz/gitlabber/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/ezbz/gitlabber/compare/v1.1.9...v1.2.0
[1.1.9]: https://github.com/ezbz/gitlabber/compare/v1.1.8...v1.1.9
[1.1.8]: https://github.com/ezbz/gitlabber/compare/v1.1.7...v1.1.8
[1.1.7]: https://github.com/ezbz/gitlabber/compare/v1.1.6...v1.1.7
[1.1.6]: https://github.com/ezbz/gitlabber/compare/v1.1.4...v1.1.6
[1.1.4]: https://github.com/ezbz/gitlabber/compare/v1.1.3...v1.1.4
[1.1.3]: https://github.com/ezbz/gitlabber/compare/v1.1.2...v1.1.3
[1.1.2]: https://github.com/ezbz/gitlabber/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/ezbz/gitlabber/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/ezbz/gitlabber/compare/v1.0.9...v1.1.0
[1.0.9]: https://github.com/ezbz/gitlabber/compare/v1.0.8...v1.0.9
[1.0.8]: https://github.com/ezbz/gitlabber/releases/tag/v1.0.8
