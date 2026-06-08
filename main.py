import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication

from devcommandcenter.database.connection import init_db, SessionLocal
from devcommandcenter.services.command_service import CommandService
from devcommandcenter.ui.main_window import MainWindow


def seed_if_empty() -> None:
    session = SessionLocal()
    try:
        service = CommandService(session)
        if not service.get_all():
            service.create({
                "name": "Hello World",
                "description": "Simple echo test",
                "command": "python",
                "arguments": ["-c", "import time; [print(f'Hello {i}') or time.sleep(0.5) for i in range(5)]"],
                "working_directory": sys.path[0],
                "tags": ["demo"],
            })
            service.create({
                "name": "List Files",
                "description": "List current directory",
                "command": "python",
                "arguments": ["-c", "import os; print('\\n'.join(os.listdir('.')))"],
                "working_directory": sys.path[0],
                "tags": ["demo", "filesystem"],
            })
    finally:
        session.close()


def _load_icon() -> QIcon:
    icon = QIcon()
    svg_path = Path(__file__).parent / "assets" / "logo.svg"
    if not svg_path.exists():
        return icon
    renderer = QSvgRenderer(str(svg_path))
    for size in (16, 24, 32, 48, 64, 128, 256, 512):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        icon.addPixmap(pixmap)
    return icon


def main() -> None:
    init_db()
    seed_if_empty()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    icon = _load_icon()
    app.setWindowIcon(icon)
    window = MainWindow()
    window.setWindowIcon(icon)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
