import logging
import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication, QMessageBox

from devcommandcenter.config import DATABASE_URL, resource_path
from devcommandcenter.database.connection import SessionLocal, init_db
from devcommandcenter.services.command_service import CommandService
from devcommandcenter.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def _set_windows_app_id() -> None:
    """Tell Windows to treat this process as its own app so the taskbar
    shows our icon instead of the generic python.exe icon."""
    try:
        import ctypes
        app_id = "MathiasPaulenko.DevCommandCenter.1.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass


def _safe_cwd() -> str:
    try:
        return os.getcwd()
    except OSError:
        return str(Path.home())


def seed_if_empty() -> None:
    session = SessionLocal()
    try:
        service = CommandService(session)
        if not service.get_all():
            cwd = _safe_cwd()
            service.create({
                "name": "Hello World",
                "description": "Simple echo test",
                "command": "python",
                "arguments": ["-c", "import time; [print(f'Hello {i}') or time.sleep(0.5) for i in range(5)]"],
                "working_directory": cwd,
            })
            service.create({
                "name": "List Files",
                "description": "List current directory",
                "command": "python",
                "arguments": ["-c", "import os; print('\\n'.join(os.listdir('.')))"],
                "working_directory": cwd,
            })
    finally:
        session.close()


def _sqlite_file_from_url(url: str) -> Path | None:
    """Filesystem path behind a ``sqlite://`` URL, or None for in-memory
    databases and non-sqlite URLs."""
    if not url.startswith("sqlite://") or ":memory:" in url:
        return None
    rest = url[len("sqlite://"):]
    if rest.startswith("//"):
        return Path(rest[1:])  # sqlite:////abs/path
    if len(rest) > 2 and rest[0] == "/" and rest[2] == ":":
        return Path(rest[1:])  # sqlite:///C:/... — Windows absolute path
    return Path(rest.lstrip("/"))


def _init_database() -> bool:
    """Create the schema and seed data, recovering from a corrupted DB file.

    Returns False only when even a fresh database can't be initialized —
    the caller shows an error and exits.
    """
    try:
        init_db()
        seed_if_empty()
        return True
    except Exception:
        logger.exception("Database initialization failed; attempting recovery")

    # A corrupted sqlite file makes init fail before the app can show
    # anything — move it aside and try once more with a fresh database.
    try:
        db_file = _sqlite_file_from_url(DATABASE_URL)
        if db_file is not None and db_file.is_file():
            backup = db_file.with_name(
                f"{db_file.stem}.corrupt-{int(time.time())}{db_file.suffix}"
            )
            db_file.rename(backup)
            logger.warning("Moved corrupted database aside to %s", backup)
        init_db()
        seed_if_empty()
        return True
    except Exception:
        logger.exception("Database recovery failed")
        QMessageBox.critical(
            None,
            "Database Error",
            "DevCommandCenter could not initialize its database.\n"
            "Check the log for details.",
        )
        return False


def _load_icon() -> QIcon:
    icon = QIcon()
    svg_path = resource_path("assets/logo.svg")
    if not svg_path.exists():
        return icon
    renderer = QSvgRenderer(str(svg_path))
    for size in (16, 24, 32, 48, 64, 128, 256, 512):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        # scale the SVG to the target rect; render() without bounds would
        # draw at defaultSize and clip anything smaller than it
        renderer.render(painter, QRectF(0, 0, size, size))
        painter.end()
        icon.addPixmap(pixmap)
    return icon


def main() -> None:
    _set_windows_app_id()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    icon = _load_icon()
    app.setWindowIcon(icon)
    if not _init_database():
        sys.exit(1)
    window = MainWindow()
    window.setWindowIcon(icon)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
