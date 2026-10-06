import shutil
import sys
from datetime import datetime
from enum import Enum

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal


class ProcessState(Enum):
    STOPPED = "Stopped"
    RUNNING = "Running"
    FAILED = "Failed"


class ManagedProcess(QObject):
    stateChanged = Signal(str, str)  # command_id, state
    outputReady = Signal(str, str)  # command_id, text
    errorReady = Signal(str, str)  # command_id, text
    logReady = Signal(str, str, str, int, object)  # command_id, stdout, stderr, exit_code, started_at

    def __init__(self, command_id: int, command: str, arguments: list,
                 working_directory: str, env_vars: dict) -> None:
        super().__init__()
        self.command_id = str(command_id)
        self.state = ProcessState.STOPPED
        self._stdout_buffer: list[str] = []
        self._stderr_buffer: list[str] = []
        self._stopping = False
        self._log_emitted = False
        self._started_at: datetime | None = None

        resolved_command, resolved_args = self._resolve_command(command, arguments)
        self.process = QProcess(self)
        self.process.setProgram(resolved_command)
        self.process.setArguments([str(a) for a in resolved_args])
        if working_directory:
            self.process.setWorkingDirectory(working_directory)

        if env_vars:
            environment = QProcessEnvironment.systemEnvironment()
            for key, value in env_vars.items():
                environment.insert(str(key), str(value))
            self.process.setProcessEnvironment(environment)

        self.process.readyReadStandardOutput.connect(self._on_stdout)
        self.process.readyReadStandardError.connect(self._on_stderr)
        self.process.finished.connect(self._on_finished)
        self.process.errorOccurred.connect(self._on_error)

    def start(self) -> bool:
        if self.process.state() != QProcess.ProcessState.NotRunning:
            return False
        self._stopping = False
        self._log_emitted = False
        self._started_at = datetime.now()
        self._set_state(ProcessState.RUNNING)
        self.process.start()
        return True

    def stop(self) -> None:
        if self.process.state() == QProcess.ProcessState.NotRunning:
            self._set_state(ProcessState.STOPPED)
            return
        self._stopping = True
        self.process.terminate()
        QTimer.singleShot(3000, self._force_kill_if_running)

    def _force_kill_if_running(self) -> None:
        if self.process.state() != QProcess.ProcessState.NotRunning:
            self.process.kill()

    def _set_state(self, state: ProcessState) -> None:
        if self.state != state:
            self.state = state
            self.stateChanged.emit(self.command_id, self.state.value)

    def _emit_log_once(self, exit_code: int) -> None:
        """Persist the run exactly once.

        A crash makes Qt emit both errorOccurred and finished; without the
        guard we'd write two log rows for a single execution.
        """
        if self._log_emitted:
            return
        self._log_emitted = True
        self.logReady.emit(
            self.command_id,
            "".join(self._stdout_buffer),
            "".join(self._stderr_buffer),
            exit_code,
            self._started_at or datetime.now(),
        )
        self._stdout_buffer.clear()
        self._stderr_buffer.clear()

    def _on_stdout(self) -> None:
        data = self.process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        self._stdout_buffer.append(data)
        self.outputReady.emit(self.command_id, data)

    def _on_stderr(self) -> None:
        data = self.process.readAllStandardError().data().decode("utf-8", errors="replace")
        self._stderr_buffer.append(data)
        self.errorReady.emit(self.command_id, data)

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        # On Windows terminate() equals kill(), so a user-initiated stop arrives
        # here as CrashExit — honour the stop intent instead of flagging Failed.
        if self._stopping or (exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit):
            self._set_state(ProcessState.STOPPED)
        else:
            self._set_state(ProcessState.FAILED)
        self._emit_log_once(exit_code)

    def _resolve_command(self, command: str, arguments: list) -> tuple[str, list]:
        arguments = arguments or []
        if sys.platform == "win32" and not command.lower().endswith(".exe"):
            exe_path = shutil.which(command)
            if exe_path and exe_path.lower().endswith(".exe"):
                return exe_path, arguments
            return "cmd.exe", ["/c", command, *arguments]
        return command, arguments

    def _on_error(self, error: QProcess.ProcessError) -> None:
        error_msg = {
            QProcess.ProcessError.FailedToStart: (
                f"Failed to start '{self.process.program()}': "
                "program not found or insufficient permissions."
            ),
            QProcess.ProcessError.Crashed: "Process crashed unexpectedly.",
            QProcess.ProcessError.Timedout: "Process timed out.",
            QProcess.ProcessError.ReadError: "Read error from process.",
            QProcess.ProcessError.WriteError: "Write error to process.",
            QProcess.ProcessError.UnknownError: f"Unknown process error ({error}).",
        }.get(error, f"Process error: {error}")
        self._stderr_buffer.append(error_msg)
        self.errorReady.emit(self.command_id, error_msg)
        self._set_state(ProcessState.FAILED)
        # Crashed is always followed by finished(), which writes the real exit
        # code. For the rest there may be no finished(), so log now.
        if error != QProcess.ProcessError.Crashed:
            self._emit_log_once(-1)


class ProcessService(QObject):
    stateChanged = Signal(str, str)
    outputReady = Signal(str, str)
    errorReady = Signal(str, str)
    logReady = Signal(str, str, str, int, object)

    def __init__(self) -> None:
        super().__init__()
        self._processes: dict[str, ManagedProcess] = {}

    def start(self, command_id: int, command: str, arguments: list,
              working_directory: str, env_vars: dict) -> bool:
        cid = str(command_id)
        if cid in self._processes and self._processes[cid].state == ProcessState.RUNNING:
            return False
        if cid in self._processes:
            old = self._processes[cid]
            old.stateChanged.disconnect(self.stateChanged)
            old.outputReady.disconnect(self.outputReady)
            old.errorReady.disconnect(self.errorReady)
            old.logReady.disconnect(self.logReady)
            del self._processes[cid]

        proc = ManagedProcess(command_id, command, arguments, working_directory, env_vars)
        proc.stateChanged.connect(self.stateChanged)
        proc.outputReady.connect(self.outputReady)
        proc.errorReady.connect(self.errorReady)
        proc.logReady.connect(self.logReady)
        self._processes[cid] = proc
        return proc.start()

    def stop(self, command_id: int) -> None:
        cid = str(command_id)
        proc = self._processes.get(cid)
        if proc:
            proc.stop()

    def stop_all(self) -> None:
        for proc in self._processes.values():
            proc.stop()

    def has_running(self) -> bool:
        return any(
            proc.process.state() != QProcess.ProcessState.NotRunning
            for proc in self._processes.values()
        )

    def get_state(self, command_id: int) -> str:
        cid = str(command_id)
        proc = self._processes.get(cid)
        return proc.state.value if proc else ProcessState.STOPPED.value
