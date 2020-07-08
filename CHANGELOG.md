# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 0.2.0 - 2020-07-08

### Added

- Add support for watching multiple directories, each with its own reload callbacks. (Pull #15)

### Changed

- `arel.HotReload("./directory", on_reload=[...])` should now be written as `arel.HotReload(paths=[arel.Path("./directory", on_reload=[...])])`. (Pull #15)

## 0.1.0 - 2020-04-11

_Initial release._

### Added

- Add `HotReload` ASGI application class. (Pull #1)
