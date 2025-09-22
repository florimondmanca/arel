# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 0.4.0 - 2025-09-22

### Removed

- Drop support for Python 3.7 and 3.8 (EOL versions). (Pull #39)

### Added

- Add support for Python 3.13. (Pull #39)

### Fixed

- Update watchfiles dependency to support modern versions (>=0.18,<2.0). (Pull #39)

## 0.3.0 - 2023-12-29

### Changed

- Use `watchfiles` instead of `watchgod`. This unlocks Python 3.12 support. (Pull #34)

### Added

- Add support for Python 3.12. (Pull #35)

## 0.2.0 - 2020-07-08

### Added

- Add support for watching multiple directories, each with its own reload callbacks. (Pull #15)

### Changed

- `arel.HotReload("./directory", on_reload=[...])` should now be written as `arel.HotReload(paths=[arel.Path("./directory", on_reload=[...])])`. (Pull #15)

## 0.1.0 - 2020-04-11

_Initial release._

### Added

- Add `HotReload` ASGI application class. (Pull #1)
