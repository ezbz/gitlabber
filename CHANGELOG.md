# Changelog

<!--next-version-placeholder-->
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

[unreleased]: https://github.com/ezbz/gitlabber/compare/v1.1.8...HEAD
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
