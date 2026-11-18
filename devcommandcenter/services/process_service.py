import codecs
import shutil
import sys
from datetime import datetime
from enum import Enum

from PySide6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, Signal

# Cap how much of a runaway process' output is kept in memory and persisted —
# an unbounded buffer turns `yes` into an out-of-memory / multi-GB log row.
MAX_OUTPUT_CHARS = 4_000_000
TRUNCATED_NOTE = "[… output truncated, keeping the last part …]\n"


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
        self._stdout_len = 0
        self._stderr_len = 0
        self._stdout_truncated = False
        self._stderr_truncated = False
        # Incremental decoders keep multibyte UTF-8 characters intact even when
        # a pipe read splits them across chunks.
        self._stdout_decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._stderr_decoder = codecs.getincrementaldecoder("utf-8")("replace")
        self._stopping = False
        self._log_emitted = False
        self._started_at: datetime | None = None

        resolved_command, resolved_args = self._resolve_command(str(command), arguments)
        self.process = QProcess(self)
        self.process.setProgram(resolved_command)
        self.process.setArguments([str(a) for a in resolved_args])
        if working_directory:
            self.process.setWorkingDirectory(str(working_directory))

        # env_vars/arguments may hold legacy rows written before validation
        # existed — never let a bad shape crash the launcher.
        if isinstance(env_vars, dict) and env_vars:
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
        self._stdout_buffer.clear()
        self._stderr_buffer.clear()
        self._stdout_len = 0
        self._stderr_len = 0
        self._stdout_truncated = False
        self._stderr_truncated = False
        self._stdout_decoder.reset()
        self._stderr_decoder.reset()
        self._set_state(ProcessState.RUNNING)
        self.process.start()
        return True

    def stop(self) -> None:
        if self.process.state() == QProcess.ProcessState.NotRunning:
            # Only a live process can be stopped — don't rewrite a Failed
            # state into Stopped.
            if self.state == ProcessState.RUNNING:
                self._set_state(ProcessState.STOPPED)
            return
        self._stopping = True
        self.process.terminate()
        QTimer.singleShot(3000, self._force_kill_if_running)

    def _force_kill_if_running(self) -> None:
        if self._stopping and self.process.state() != QProcess.ProcessState.NotRunning:
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
        stdout = "".join(self._stdout_buffer)
        stderr = "".join(self._stderr_buffer)
        if self._stdout_truncated:
            stdout = TRUNCATED_NOTE + stdout
        if self._stderr_truncated:
            stderr = TRUNCATED_NOTE + stderr
        self.logReady.emit(
            self.command_id,
            stdout,
            stderr,
            exit_code,
            self._started_at or datetime.now(),
        )
        self._stdout_buffer.clear()
        self._stderr_buffer.clear()
        self._stdout_len = 0
        self._stderr_len = 0
        self._stdout_truncated = False
        self._stderr_truncated = False

    def _buffer(self, text: str, *, stdout: bool) -> None:
        """Append decoded text, dropping the oldest chunks past the cap."""
        buf = self._stdout_buffer if stdout else self._stderr_buffer
        buf.append(text)
        total = (self._stdout_len if stdout else self._stderr_len) + len(text)
        if total > MAX_OUTPUT_CHARS:
            drop = total - MAX_OUTPUT_CHARS
            while drop > 0 and buf:
                if len(buf[0]) <= drop:
                    drop -= len(buf.pop(0))
                else:
                    buf[0] = buf[0][drop:]
                    drop = 0
            if stdout:
                self._stdout_truncated = True
            else:
                self._stderr_truncated = True
            total = MAX_OUTPUT_CHARS
        if stdout:
            self._stdout_len = total
        else:
            self._stderr_len = total

    def _on_stdout(self) -> None:
        data = self._stdout_decoder.decode(self.process.readAllStandardOutput().data())
        if not data:
            return
        self._buffer(data, stdout=True)
        self.outputReady.emit(self.command_id, data)

    def _on_stderr(self) -> None:
        data = self._stderr_decoder.decode(self.process.readAllStandardError().data())
        if not data:
            return
        self._buffer(data, stdout=False)
        self.errorReady.emit(self.command_id, data)

    def _drain_channel(self, *, stdout: bool) -> None:
        """Read whatever is left on a channel and flush the decoder tail.

        On a crash some output can remain unread when finished() fires, and a
        multibyte char can end the stream mid-sequence.
        """
        if stdout:
            data = self.process.readAllStandardOutput().data()
            tail = self._stdout_decoder.decode(data, final=True)
        else:
            data = self.process.readAllStandardError().data()
            tail = self._stderr_decoder.decode(data, final=True)
        if not tail:
            return
        self._buffer(tail, stdout=stdout)
        if stdout:
            self.outputReady.emit(self.command_id, tail)
        else:
            self.errorReady.emit(self.command_id, tail)

    def _on_finished(self, exit_code: int, exit_status: QProcess.ExitStatus) -> None:
        self._drain_channel(stdout=True)
        self._drain_channel(stdout=False)
        # On Windows terminate() equals kill(), so a user-initiated stop arrives
        # here as CrashExit — honour the stop intent instead of flagging Failed.
        if self._stopping or (exit_code == 0 and exit_status == QProcess.ExitStatus.NormalExit):
            self._set_state(ProcessState.STOPPED)
        else:
            self._set_state(ProcessState.FAILED)
        self._emit_log_once(exit_code)

    def _resolve_command(self, command: str, arguments: list) -> tuple[str, list]:
        if not isinstance(arguments, (list, tuple)):
            arguments = [arguments] if arguments is not None else []
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
        self._stderr_len += len(error_msg)
        self.errorReady.emit(self.command_id, error_msg)
        # Crashed is always followed by finished(), which drains, sets the
        # state and writes the real exit code. For the rest there may be no
        # finished(): drain first so the flushed bytes reach listeners while
        # the state transition is still pending, then emit state and log.
        if error != QProcess.ProcessError.Crashed:
            self._drain_channel(stdout=True)
            self._drain_channel(stdout=False)
            self._set_state(ProcessState.FAILED)
            self._emit_log_once(-1)
        else:
            self._set_state(ProcessState.FAILED)


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
        if command is None or not str(command).strip():
            return False
        cid = str(command_id)
        if cid in self._processes and self._processes[cid].state == ProcessState.RUNNING:
            return False
        if cid in self._processes:
            old = self._processes[cid]
            for signal in (
                old.stateChanged, old.outputReady, old.errorReady, old.logReady,
            ):
                try:
                    signal.disconnect()
                except (RuntimeError, TypeError):
                    pass
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
