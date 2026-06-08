# DevCommandCenter

Desktop application for developers to save, run, monitor and stop frequent development commands from a single interface.

## Features

- **Command cards** with Run, Stop, Logs, Edit, Delete actions.
- **Parallel execution** — run multiple commands simultaneously without blocking.
- **Live logs** with command-name prefixes for clarity.
- **Persistent storage** via SQLite (SQLAlchemy ORM).
- **Execution history** stored per command.
- **Auto-run** commands on application startup.
- **Search/filter** by name, description or tags.
- **Import/Export** commands as JSON.
- **Dark theme** UI built with PySide6 (Qt).

## Tech Stack

- Python 3.12+
- PySide6 (Qt)
- SQLAlchemy + SQLite
- QProcess for process management

## Setup

```bash
pip install -r requirements.txt
python main.py
```

## Tests

```bash
python tests/test_mvp.py
```

## Project Structure

```text
devcommandcenter/
  database/      # SQLAlchemy models and connection
  services/      # Business logic (CRUD, process manager)
  ui/            # PySide6 widgets and dialogs
  utils/         # Shared utilities
```
