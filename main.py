import sys

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


def main() -> None:
    init_db()
    seed_if_empty()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
