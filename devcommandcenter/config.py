import os
from pathlib import Path

APP_NAME = "DevCommandCenter"
APP_VERSION = "0.2.0"

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATA_DIR / "devcommandcenter.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
