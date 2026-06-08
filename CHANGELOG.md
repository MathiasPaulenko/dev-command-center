# Changelog

All notable changes to DevCommandCenter will be documented in this file.

## [0.2.0] - 2026-06-08

### Added

- Auto-scroll logs with timestamps on every line.
- Status bar showing real-time running process count.
- Double-click card to run command.
- Copy button in historical logs dialog.
- Search/filter commands by name, description, or tags.
- Execution log persistence to SQLite on process finish.
- Per-command historical logs viewer.
- Auto-run commands on startup.
- Import/Export commands to JSON via menu bar.
- Browse button for working directory selection.
- Graceful shutdown stopping all active processes.
- Project files: .gitignore, CONTRIBUTING.md, CHANGELOG.md, .editorconfig, VERSIONING.md.
- Virtual environment setup.

### Fixed

- UI freeze when stopping processes (async kill via QTimer).
- Markdown lint warnings in documentation files.

## [0.1.0] - 2026-06-08

### Added

- Initial MVP release.
- Main window with command cards and log panel.
- CRUD for commands via modal dialog.
- Run/Stop processes using QProcess with parallel execution support.
- SQLite persistence via SQLAlchemy.
- Execution log model (ExecutionLog).
- Dark theme UI styling.
