from pathlib import Path

APP_NAME = "DevCommandCenter"
APP_VERSION = "1.1.0"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH = DATA_DIR / "devcommandcenter.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"
