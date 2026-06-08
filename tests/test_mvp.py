import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from devcommandcenter.database.connection import init_db, SessionLocal
from devcommandcenter.services.command_service import CommandService
from devcommandcenter.services.process_service import ProcessService
from PySide6.QtCore import QCoreApplication, QTimer

# Need a QCoreApplication for QProcess signals
app = QCoreApplication(sys.argv)

def test_database():
    init_db()
    session = SessionLocal()
    service = CommandService(session)

    cmd = service.create({
        "name": "Test Echo",
        "command": "python",
        "arguments": ["-c", "print('hello world')"],
        "working_directory": os.getcwd(),
    })
    assert cmd.id is not None
    print(f"Created command: {cmd.name}")

    all_cmds = service.get_all()
    assert len(all_cmds) >= 1

    updated = service.update(cmd.id, {"name": "Updated Echo"})
    assert updated.name == "Updated Echo"

    proc_service = ProcessService()
    assert proc_service.get_state(cmd.id) == "Stopped"

    ok = proc_service.start(
        cmd.id,
        "python",
        ["-c", "print('ok')"],
        os.getcwd(),
        {}
    )
    assert ok
    assert proc_service.get_state(cmd.id) == "Running"

    while proc_service.get_state(cmd.id) == "Running":
        app.processEvents()

    service.delete(cmd.id)
    session.close()
    
    print("All MVP tests passed!")

if __name__ == "__main__":
    test_database()
