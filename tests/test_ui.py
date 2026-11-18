"""UI smoke tests — exercise real widgets on the offscreen Qt platform.

Covers the MainWindow card grid, LogWindow lifecycle/signal wiring, and
CommandDialog validation/parsing.

Runs under pytest or standalone: ``python tests/test_ui.py``.
"""

import os
import sys
import tempfile
import time

# Isolate the test database and force the offscreen platform before Qt or
# devcommandcenter are imported (both bind at import/instantiation time).
_tmp_dir = tempfile.mkdtemp(prefix="dcc_ui_")
os.environ.setdefault("DCC_DATABASE_URL", f"sqlite:///{_tmp_dir}/ui.db")
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import QApplication, QDialog

from devcommandcenter.database.connection import SessionLocal, init_db
from devcommandcenter.services.command_service import CommandService
from devcommandcenter.services.process_service import ProcessService
from devcommandcenter.ui.command_dialog import CommandDialog
from devcommandcenter.ui.log_window import LogWindow
from devcommandcenter.ui.main_window import MainWindow

app = QApplication.instance() or QApplication(sys.argv)


def _seed_command(name: str = "UI Echo"):
    init_db()
    session = SessionLocal()
    try:
        return CommandService(session).create({
            "name": name,
            "command": "python",
            "arguments": ["-c", "print('ui ok')"],
        })
    finally:
        session.close()


def pump_until(cond, timeout=10.0):
    deadline = time.monotonic() + timeout
    while not cond() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    return cond()


def test_main_window_loads_seed_commands():
    cmd = _seed_command("MW Seed")
    win = MainWindow()
    try:
        assert cmd.id in win._cards
        assert win._cards[cmd.id].command_obj.name == "MW Seed"
    finally:
        win.close()


def test_log_window_stopped_shows_last_run_state():
    win = LogWindow(4242, "Nothing ran", ProcessService())
    try:
        assert win.status_label.text() == "Stopped"
        assert not win.stop_btn.isEnabled()
        assert "No previous executions" in win.output.toPlainText()
    finally:
        win.close()


def test_log_window_shows_persisted_last_execution():
    init_db()
    session = SessionLocal()
    try:
        from devcommandcenter.services.execution_log_service import (
            ExecutionLogService,
        )
        ExecutionLogService(session).create({
            "command_id": 777, "output": "persisted line", "exit_code": 0,
        })
    finally:
        session.close()
    win = LogWindow(777, "Has history", ProcessService())
    try:
        assert "persisted line" in win.output.toPlainText()
    finally:
        win.close()


def test_log_window_receives_live_output_and_disconnects():
    ps = ProcessService()
    win = LogWindow(555, "Live", ps)
    ps.start(555, "python", ["-c", "print('live-line-xyz')"], "", {})
    try:
        ok = pump_until(lambda: "live-line-xyz" in win.output.toPlainText(), 15)
        assert ok
        assert win.status_label.text() in ("Running", "Stopped")
    finally:
        ps.stop(555)
        win.close()
    # After close the window must not stay connected (it is delete-on-close).
    assert not win._signals_connected


def test_command_dialog_parses_fields_and_drops_bad_json():
    dlg = CommandDialog()
    try:
        dlg.name_input.setText("x")
        dlg.command_input.setText("python")
        dlg.args_input.setText('["-c", "print(1)"]')
        dlg.env_input.setPlainText('{"A": "1"}')
        data = dlg.get_data()
        assert data["arguments"] == ["-c", "print(1)"]
        assert data["env_vars"] == {"A": "1"}

        dlg.args_input.setText("not json")
        dlg.env_input.setPlainText("[1, 2]")
        data = dlg.get_data()
        assert data["arguments"] == []
        assert data["env_vars"] == {}
    finally:
        dlg.close()


def test_command_dialog_valid_input_accepts():
    dlg = CommandDialog()
    try:
        dlg.name_input.setText("ok")
        dlg.command_input.setText("python")
        dlg.accept()
        assert dlg.result() == QDialog.DialogCode.Accepted
    finally:
        dlg.close()


def _all_tests():
    return [(k, v) for k, v in sorted(globals().items())
            if k.startswith("test_") and callable(v)]


if __name__ == "__main__":
    failures = 0
    for name, fn in _all_tests():
        try:
            fn()
            print(f"PASS {name}")
        except Exception as e:
            failures += 1
            print(f"FAIL {name}: {type(e).__name__}: {e}")
    print(f"\n{len(_all_tests()) - failures} passed, {failures} failed")
    sys.exit(1 if failures else 0)
