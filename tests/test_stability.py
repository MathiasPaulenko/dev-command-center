"""Regression + hardening suite for DevCommandCenter.

Covers the bugs found in the stability audit: service-layer validation,
cascade deletes, rowid reuse, process lifecycle edge cases, output caps,
and theme/config regressions.

Runs under pytest or standalone: ``python tests/test_stability.py``.
"""

import os
import sys
import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

# Isolate the test database before devcommandcenter.config is imported —
# DATABASE_URL is read at import time.
_tmp_dir = tempfile.mkdtemp(prefix="dcc_stab_")
os.environ.setdefault("DCC_DATABASE_URL", f"sqlite:///{_tmp_dir}/test.db")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QCoreApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from devcommandcenter.database.models import Base, Command
from devcommandcenter.services.command_service import (
    CommandService,
    sanitize_command_data,
)
from devcommandcenter.services.execution_log_service import ExecutionLogService
from devcommandcenter.services.process_service import (
    MAX_OUTPUT_CHARS,
    TRUNCATED_NOTE,
    ManagedProcess,
    ProcessService,
)
from devcommandcenter.ui.command_card import _relative_time
from devcommandcenter.ui.theme import APP_STYLESHEET, SELECTION_BG

app = QCoreApplication.instance() or QCoreApplication(sys.argv)


# ---------------------------------------------------------------- helpers

def _fresh_session():
    """A session on its own throwaway file DB (no shared state between tests)."""
    path = os.path.join(_tmp_dir, f"t{time.time_ns()}.db")
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def pump_until(cond, timeout=10.0):
    deadline = time.monotonic() + timeout
    while not cond() and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    return cond()


# ---------------------------------------------------- service validation

def test_create_rejects_blank_name():
    session = _fresh_session()
    for bad in ["", "   ", "\t\n", None, 123]:
        try:
            CommandService(session).create({"name": bad, "command": "python"})
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted bad name {bad!r}")
    session.close()


def test_create_rejects_missing_fields_and_blank_command():
    session = _fresh_session()
    svc = CommandService(session)
    for bad in [
        {},
        {"name": "x"},
        {"command": "python"},
        {"name": "x", "command": ""},
        {"name": "x", "command": "   "},
    ]:
        try:
            svc.create(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted {bad!r}")
    session.close()


def test_create_drops_unknown_keys_and_strips_name():
    session = _fresh_session()
    cmd = CommandService(session).create(
        {"name": "  padded  ", "command": "python", "bogus": 1, "id": 777}
    )
    assert cmd.name == "padded"
    assert cmd.id != 777
    session.close()


def test_create_validates_arguments_env_vars_tags_types():
    session = _fresh_session()
    svc = CommandService(session)
    base = {"name": "x", "command": "python"}
    for field, value in [("arguments", "abc"), ("env_vars", [1]), ("tags", "nope")]:
        try:
            svc.create({**base, field: value})
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted {field}={value!r}")
    # valid values still accepted
    cmd = svc.create({**base, "arguments": ["-c", "x"], "env_vars": {"A": "1"},
                      "tags": ["t"], "auto_run": 1})
    assert cmd.auto_run is True
    session.close()


def test_update_cannot_overwrite_identity_fields():
    session = _fresh_session()
    svc = CommandService(session)
    cmd = svc.create({"name": "orig", "command": "python"})
    original_created = cmd.created_at
    out = svc.update(cmd.id, {"id": 9999, "created_at": "2000-01-01",
                              "updated_at": "2000-01-01", "name": "new"})
    assert out.name == "new"
    assert out.id == cmd.id
    assert svc.get_by_id(9999) is None
    assert out.created_at == original_created
    session.close()


def test_create_many_is_atomic():
    session = _fresh_session()
    svc = CommandService(session)
    try:
        svc.create_many([
            {"name": "good1", "command": "python"},
            {"name": "   ", "command": "python"},  # invalid
            {"name": "good2", "command": "python"},
        ])
    except ValueError:
        pass
    else:
        raise AssertionError("invalid item accepted")
    assert svc.get_all() == []
    session.close()


def test_delete_cascades_execution_logs():
    session = _fresh_session()
    svc = CommandService(session)
    logs = ExecutionLogService(session)
    cmd = svc.create({"name": "victim", "command": "python"})
    logs.create({"command_id": cmd.id, "output": "old output", "exit_code": 0})
    assert svc.delete(cmd.id) is True
    assert logs.get_by_command_id(cmd.id) == []
    session.close()


def test_new_command_does_not_inherit_deleted_ids_logs():
    session = _fresh_session()
    svc = CommandService(session)
    logs = ExecutionLogService(session)
    victim = svc.create({"name": "victim", "command": "python"})
    logs.create({"command_id": victim.id, "output": "secret", "exit_code": 0})
    svc.delete(victim.id)
    fresh = svc.create({"name": "fresh", "command": "python"})
    assert fresh.id != victim.id  # sqlite_autoincrement prevents rowid reuse
    assert logs.get_by_command_id(fresh.id) == []
    session.close()


def test_log_service_requires_command_id_and_filters_keys():
    session = _fresh_session()
    logs = ExecutionLogService(session)
    try:
        logs.create({"output": "x"})
    except ValueError:
        pass
    else:
        raise AssertionError("log without command_id accepted")
    log = logs.create({"command_id": 42, "output": "x", "bogus": "y"})
    assert log.command_id == 42
    session.close()


def test_sanitize_partial_allows_field_subset():
    clean = sanitize_command_data({"description": "only this"}, partial=True)
    assert clean == {"description": "only this"}
    clean = sanitize_command_data({"auto_run": "yes"}, partial=True)
    assert clean == {"auto_run": True}


def test_sanitize_rejects_non_dict():
    for bad in [[], "x", None, 42]:
        try:
            sanitize_command_data(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted {bad!r}")


def test_history_queries_are_bounded():
    session = _fresh_session()
    svc = CommandService(session)
    logs = ExecutionLogService(session)
    cmd = svc.create({"name": "hist", "command": "python"})
    base = datetime(2024, 1, 1)
    for i in range(10):
        logs.create({"command_id": cmd.id, "output": f"o{i}", "exit_code": 0,
                     "started_at": base + timedelta(seconds=i)})
    assert len(logs.get_by_command_id(cmd.id)) == 10
    limited = logs.get_by_command_id(cmd.id, limit=3)
    assert len(limited) == 3
    # summaries carry no output payload — just metadata + the row id
    rows = logs.get_summaries(cmd.id, limit=2)
    assert len(rows) == 2
    log_id, _started_at, _finished_at, exit_code = rows[0]
    assert isinstance(log_id, int) and exit_code == 0
    full = logs.get_by_id(log_id)
    assert full.output == "o9"  # newest first
    assert logs.get_by_id(999999) is None
    session.close()


def test_log_create_rejects_null_command_id():
    session = _fresh_session()
    logs = ExecutionLogService(session)
    for bad in [{}, {"command_id": None}, {"output": "x"}]:
        try:
            logs.create(bad)
        except ValueError:
            pass
        else:
            raise AssertionError(f"accepted {bad!r}")
    session.close()


def test_sqlite_file_from_url_parses_paths():
    from devcommandcenter.cli import _sqlite_file_from_url
    assert _sqlite_file_from_url("sqlite:///:memory:") is None
    assert _sqlite_file_from_url("postgresql://u@h/db") is None
    assert _sqlite_file_from_url("sqlite:///rel/x.db") == Path("rel/x.db")
    assert _sqlite_file_from_url("sqlite:////tmp/x.db") == Path("/tmp/x.db")
    win = _sqlite_file_from_url("sqlite:///C:/data/x.db")
    assert str(win) in ("C:/data/x.db", "C:\\data\\x.db")


# ------------------------------------------------------ process service

def test_start_rejects_empty_command():
    ps = ProcessService()
    assert ps.start(1, "", [], "", {}) is False
    assert ps.start(1, "   ", [], "", {}) is False
    assert ps.start(1, None, [], "", {}) is False


def test_stop_keeps_failed_state():
    ps = ProcessService()
    assert ps.start(3, "python", ["-c", "import sys; sys.exit(3)"], "", {})
    assert pump_until(lambda: ps.get_state(3) == "Failed", 15)
    ps.stop(3)
    pump_until(lambda: False, 0.3)
    assert ps.get_state(3) == "Failed", "stop() erased the failure state"


def test_stop_on_never_started_is_noop():
    ps = ProcessService()
    ps.stop(999)  # must not raise
    assert ps.get_state(999) == "Stopped"


def test_failed_process_emits_single_log():
    ps = ProcessService()
    logs = []
    ps.logReady.connect(lambda *a: logs.append(a))
    ps.start(4, "python", ["-c", "import sys; sys.exit(2)"], "", {})
    assert pump_until(lambda: logs, 15)
    pump_until(lambda: False, 0.3)
    for _ in range(5):
        app.processEvents()
    assert len(logs) == 1
    assert logs[0][3] == 2  # exit code propagated


def test_failing_to_start_emits_single_log():
    ps = ProcessService()
    logs, states = [], []
    ps.logReady.connect(lambda *a: logs.append(a))
    ps.stateChanged.connect(lambda cid, s: states.append(s))
    # a .exe that does not exist bypasses the cmd.exe shim -> FailedToStart
    ps.start(5, "no-such-program-xyz-123.exe", [], "", {})
    assert pump_until(lambda: ps.get_state(5) == "Failed", 15)
    pump_until(lambda: False, 0.3)
    for _ in range(5):
        app.processEvents()
    assert len(logs) == 1
    assert logs[0][3] == -1
    assert "Failed" in states


def test_restart_after_stop_creates_fresh_process():
    ps = ProcessService()
    ps.start(6, "python", ["-c", "print('a')"], "", {})
    assert pump_until(lambda: ps.get_state(6) != "Running", 15)
    first = ps._processes["6"]
    ps.start(6, "python", ["-c", "print('b')"], "", {})
    assert pump_until(lambda: ps.get_state(6) != "Running", 15)
    assert ps._processes["6"] is not first
    assert ps.get_state(6) == "Stopped"


def test_output_is_capped_with_truncation_note():
    ps = ProcessService()
    logs = []
    ps.logReady.connect(lambda *a: logs.append(a))
    ps.start(7, "python", ["-c", f"print('x' * {MAX_OUTPUT_CHARS + 1_000_000})"], "", {})
    assert pump_until(lambda: logs, 60)
    out = logs[0][1]
    assert len(out) <= MAX_OUTPUT_CHARS + len(TRUNCATED_NOTE)
    assert out.startswith(TRUNCATED_NOTE)


def test_incremental_decoder_keeps_split_utf8_intact():
    mp = ManagedProcess(8, "python", [], "", {})
    part1 = mp._stdout_decoder.decode(b"\xe2\x82")
    part2 = mp._stdout_decoder.decode(b"\xac")
    tail = mp._stdout_decoder.decode(b"", final=True)
    assert part1 + part2 + tail == "€"


def test_manual_stop_marks_stopped_not_failed():
    ps = ProcessService()
    assert ps.start(11, "python", ["-c", "import time; time.sleep(30)"], "", {})
    assert pump_until(lambda: ps.get_state(11) == "Running", 10)
    ps.stop(11)
    # terminate() + 3s force-kill fallback must land on Stopped, not Failed
    assert pump_until(lambda: ps.get_state(11) != "Running", 15)
    assert ps.get_state(11) == "Stopped"


def test_simultaneous_processes_are_independent():
    ps = ProcessService()
    assert ps.start(20, "python", ["-c", "import time; time.sleep(0.2)"], "", {})
    assert ps.start(21, "python", ["-c", "import sys; sys.exit(1)"], "", {})
    assert pump_until(
        lambda: ps.get_state(20) != "Running" and ps.get_state(21) != "Running", 20
    )
    assert ps.get_state(20) == "Stopped"
    assert ps.get_state(21) == "Failed"


def test_stderr_is_captured_and_logged():
    ps = ProcessService()
    logs = []
    ps.logReady.connect(lambda *a: logs.append(a))
    ps.start(22, "python",
             ["-c", "import sys; sys.stderr.write('oops-err'); sys.exit(1)"], "", {})
    assert pump_until(lambda: logs, 15)
    assert "oops-err" in logs[0][2]
    assert logs[0][3] == 1


def test_env_vars_and_args_coerced_to_str():
    mp = ManagedProcess(9, "python", ["-c", "pass"], "", {1: True, "K": 2})
    env = mp.process.processEnvironment()
    assert env.contains("K")
    assert env.contains("1")


# ------------------------------------------------------------- ui utils

def test_relative_time_handles_future_timestamps():
    assert _relative_time(datetime.now() + timedelta(hours=1)) == "just now"
    assert _relative_time(None) == "never"
    assert _relative_time(datetime.now() - timedelta(minutes=5)) == "5m ago"


def test_selection_color_uses_alpha_first_hex():
    # Qt reads 8-digit hex as #AARRGGBB; the accent must keep its hue.
    from PySide6.QtGui import QColor
    c = QColor(SELECTION_BG)
    assert c.isValid()
    r, g, b, a = c.getRgb()
    assert (r, g, b) == (0x44, 0x93, 0xF8), f"selection color drifted: {c.getRgb()}"
    assert a < 255
    assert "{ACCENT}33" not in APP_STYLESHEET


def test_memory_db_engine_keeps_tables_across_sessions():
    from devcommandcenter.database.connection import _make_engine
    engine = _make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    S = sessionmaker(bind=engine)
    s1 = S()
    s1.add(Command(name="a", command="x"))
    s1.commit()
    s1.close()
    s2 = S()
    try:
        assert s2.query(Command).count() == 1
    finally:
        s2.close()


def test_models_use_sqlite_autoincrement():
    assert Command.__table_args__.get("sqlite_autoincrement") is True


# ------------------------------------------------------------- runner

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
