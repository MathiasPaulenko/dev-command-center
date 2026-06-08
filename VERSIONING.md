# Versioning Policy

DevCommandCenter follows [Semantic Versioning](https://semver.org/) (`MAJOR.MINOR.PATCH`).

## Version Bumps

| Level | When to bump | Examples |
| --- | --- | --- |
| **MAJOR** (`X.0.0`) | Breaking architectural changes that can break compatibility with previous versions. | Migration to a new database engine, removal of public APIs, major UI framework change. |
| **MINOR** (`0.X.0`) | New features, significant refactors, or notable enhancements. | New command features, new UI panels, execution sequences, grouping, import/export formats. |
| **PATCH** (`0.0.X`) | Bug fixes, minor improvements, documentation fixes, small UI tweaks. | Fixing a crash, correcting a button state, improving error messages, updating README. |

## Workflow

- The current version lives in `devcommandcenter/config.py` as the single source of truth.
- On every significant change, this file and `CHANGELOG.md` are updated.
- The version is **bumped before** releasing or tagging, not after.

## Current Version

`0.2.0`
