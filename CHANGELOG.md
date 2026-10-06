# Changelog

All notable changes to DevCommandCenter will be documented in this file.

## [1.3.0] - 2026-10-06

### Fixed

- Reopening a log window no longer leaves it disconnected from live output (windows are now deleted on close and recreated fresh).
- Log window now reflects the real process state when opened (status label and Stop button are initialized correctly).
- Manually stopping a command on Windows no longer marks it as Failed.
- A crashing process no longer writes duplicate log entries.
- `started_at` in execution logs now records the real start time instead of the insert time.
- Arguments/env vars are validated as JSON array/object in the command dialog.
- Command description and env vars no longer get mangled when they contain HTML-like text.
- App icon and About logo are no longer cropped at small sizes (SVG now renders scaled to the target rect).
- Deleting a command now also removes its execution logs and closes its log window.
- Import validates that the JSON is an array of commands with `name` and `command`.
- ANSI escape sequences that are not color codes no longer leak as garbage into the log output.
- Log lines split across output chunks no longer get fragmented timestamps.
- Command names and descriptions can no longer inject rich text into labels.
- The database no longer lives inside the PyInstaller temp dir (it moved to the user data dir for packaged builds).
- Bundled assets now actually ship in the executable (`--add-data` in all build paths, matching `resource_path`).
- `build.bat` now builds `main.py` so package imports resolve.
- The status bar command count now refreshes after create/delete/import (it only updated on state changes before).
- Timestamps are stored as naive local time consistently, so "Last run" relative times are correct in any timezone.

### Changed

- Added `scripts/manual_e2e.py` — a pywinauto/UIA walkthrough that drives the real GUI (run/stop, log windows, dialogs, filters, delete) and saves screenshots to `e2e_artifacts/`.

- Split `main_window.py` into `command_card.py`, `history_dialog.py`, and `about_dialog.py`.
- `__version__` now derives from `APP_VERSION` (single source of truth).
- Tests run against an isolated database (`DCC_DATABASE_URL`) instead of the real one.

### Removed

- Duplicate release workflow (`release.yml`); `build-release.yml` now handles builds and the GitHub Release.
- Dead code: unused theme aliases, `card_stylesheet`, `tag_chip_stylesheet`, `_command_names`, unused imports.

### Added

- **Pip installable** — `pip install git+https://github.com/MathiasPaulenko/dev-command-center.git` works. Entry points: `devcommandcenter` and `dcc`.
- **`python -m devcommandcenter`** — module execution via `__main__.py`.

### Changed

- **Package restructure** — `assets/logo.svg` moved inside `devcommandcenter/assets/` for proper packaging.
- **`main.py`** — simplified to a thin wrapper importing `devcommandcenter.cli:main`.
- **`BASE_DIR`** — now points to the package root so data directory resolves correctly when installed.

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
