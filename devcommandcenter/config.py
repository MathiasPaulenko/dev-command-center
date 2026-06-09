import sys
from pathlib import Path

APP_NAME = "DevCommandCenter"
APP_VERSION = "1.2.0"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"


def resource_path(relative_path: str) -> Path:
    """Return the absolute path to a bundled resource.

    Works both in development and when packaged by PyInstaller
    (onefile or onedir).
    """
    if hasattr(sys, "_MEIPASS"):
        return Path(getattr(sys, "_MEIPASS")) / relative_path
    return BASE_DIR / relative_path


DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_PATH = DATA_DIR / "devcommandcenter.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
