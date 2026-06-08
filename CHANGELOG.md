# Changelog

All notable changes to DevCommandCenter will be documented in this file.

## [1.1.0] - 2026-06-08

### Added

- **Clear History** — added "Clear History" button to the Execution History dialog with confirmation dialog and full database deletion for that command.
- **Signal-based refresh** — clearing history automatically updates the "Last run" label on the corresponding card.

### Changed

- **Options menu** — collapsed secondary card buttons (Logs, History, Edit, Duplicate, Delete) into a discreet `⋮` icon in the top-right corner of each card, reducing visual clutter.
- **Card spacing** — increased body margins (`22px`), spacing (`14px`), divider margins, button heights (`34px`), and grid gap (`20px`) for a less cramped layout.
- **Sidebar brand** — redesigned from two-line "DevCmd\nCenter" to single-line "DevCommandCenter" with a blue accent underline bar.
- **Version label** — moved from sidebar to status bar as a permanent widget at the bottom-right of the window.
- **Search placeholder** — simplified to "Search by name or description..." after tags removal.
- **Log window buttons** — fixed text cutoff on the "Clear" button by removing fixed width and adding consistent styling.

### Removed

- **Tags** — removed tag chips from command cards, tag editor from New/Edit dialogs, tag-based search, and tag field from duplicate/export operations.

### Fixed

- Fixed missing `BORDER_HOVER` import in `log_window.py`.
- Fixed missing `QTextEdit` import in `main_window.py`.

## [1.0.0] - 2026-06-08

### Added

- **App icon** — SVG logo rendered via `QSvgRenderer` and set on application and main window; Windows taskbar icon fixed via `AppUserModelID`.
- **Execution history dialog** — per-command history viewer with list of past runs, status coloring, and detailed output panel.
- **Last run info** — cards display human-readable relative timestamp (e.g. "5m ago") based on latest execution log.
- **Duplicate command** — "Duplicate" action in card menu to clone an existing command.
- **Colors in log window** — `stdout` in white, `stderr` in red (`#f85149`).
- **Auto-run on startup** — commands with `auto_run=True` execute automatically when the app launches.
- **Delete confirmation** — `QMessageBox.question` before removing a command.
- **About dialog** — custom `AboutDialog` with logo, version badge, features list, developer credits, MIT license, and clickable GitHub link.
- **Command dialog redesign** — spacious layout with header/footer, monospace inputs, styled tags editor, larger fields, and corrected placeholders.
- **README** — modernized with badges, tech stack table, detailed setup, architecture, and contributing sections.

### Fixed

- Fixed race condition in running process counter by removing redundant `_running_ids` manipulation in `run_command()`.
- Fixed text cut-off in About dialog by increasing height and adding word wrap.

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
