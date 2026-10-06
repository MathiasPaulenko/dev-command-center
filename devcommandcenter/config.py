import os
import sys
from pathlib import Path

APP_NAME = "DevCommandCenter"
APP_VERSION = "1.3.0"

BASE_DIR = Path(__file__).resolve().parent


def _user_data_dir() -> Path:
    """Per-user writable directory for the packaged app.

    A PyInstaller onefile build unpacks modules into a temp dir that is wiped
    on exit, so the database must live outside the bundle.
    """
    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / APP_NAME


def resource_path(relative_path: str) -> Path:
    """Return the absolute path to a bundled resource.

    Works both in development and when packaged by PyInstaller
    (onefile or onedir). Bundled resources keep the package layout
    (``devcommandcenter/`` prefix), matching the ``--add-data`` destinations
    used by the build scripts.
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")) / "devcommandcenter" / relative_path
    return BASE_DIR / relative_path


if getattr(sys, "frozen", False):
    DATA_DIR = _user_data_dir()
else:
    DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = DATA_DIR / "devcommandcenter.db"
DATABASE_URL = os.environ.get("DCC_DATABASE_URL") or f"sqlite:///{DATABASE_PATH}"
