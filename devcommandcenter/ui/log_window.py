"""Real-time log window for a single command execution."""

from datetime import datetime

from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devcommandcenter.services.process_service import ProcessService
from devcommandcenter.ui.theme import (
    ACCENT_DANGER,
    APP_STYLESHEET,
    BG_ELEVATED,
    BG_INPUT,
    BG_PRIMARY,
    BORDER,
    STATUS_FAILED,
    STATUS_RUNNING,
    STATUS_STOPPED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class LogWindow(QDialog):
    def __init__(
        self,
        command_id: int,
        command_name: str,
        process_service: ProcessService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.command_id = str(command_id)
        self.command_name = command_name
        self.process_service = process_service
        self.setWindowTitle(f"Logs: {command_name}")
        self.resize(800, 500)
        self._is_running = False
        self.setup_ui()
        self.connect_signals()
        self.update_title()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setSpacing(12)

        title = QLabel(f"<b>{self.command_name}</b>")
        title.setStyleSheet(
            f"font-size: 16px; color: {TEXT_PRIMARY}; background: transparent; border: none;"
        )
        header.addWidget(title)

        self.status_label = QLabel("Stopped")
        self.status_label.setStyleSheet(
            f"font-size: 12px; font-weight: bold; color: {TEXT_SECONDARY};"
            f"background-color: {BG_ELEVATED}; border: 1px solid {BORDER};"
            f"border-radius: 8px; padding: 4px 12px;"
        )
        header.addWidget(self.status_label)
        header.addStretch()

        self.stop_btn = QPushButton("⏹  Stop")
        self.stop_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ACCENT_DANGER}22;
                color: {ACCENT_DANGER};
                border: 1px solid {ACCENT_DANGER}44;
                border-radius: 8px;
                padding: 6px 14px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_DANGER};
                color: {BG_PRIMARY};
                border-color: {ACCENT_DANGER};
            }}
            QPushButton:disabled {{
                background-color: {BG_INPUT};
                color: {TEXT_SECONDARY};
                border-color: {BORDER};
            }}
        """
        )
        self.stop_btn.clicked.connect(self._stop_process)
        header.addWidget(self.stop_btn)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.setFixedWidth(60)
        self.clear_btn.clicked.connect(self._clear_output)
        header.addWidget(self.clear_btn)

        layout.addLayout(header)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setStyleSheet(
            f"""
            QTextEdit {{
                background-color: {BG_INPUT};
                color: {TEXT_PRIMARY};
                border: 1px solid {BORDER};
                border-radius: 10px;
                padding: 12px;
                font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
                font-size: 13px;
                line-height: 1.5;
            }}
        """
        )
        layout.addWidget(self.output, stretch=1)

        self.setStyleSheet(APP_STYLESHEET)

    def connect_signals(self) -> None:
        self.process_service.stateChanged.connect(self._on_state_changed)
        self.process_service.outputReady.connect(self._on_output)
        self.process_service.errorReady.connect(self._on_error)

    def disconnect_signals(self) -> None:
        self.process_service.stateChanged.disconnect(self._on_state_changed)
        self.process_service.outputReady.disconnect(self._on_output)
        self.process_service.errorReady.disconnect(self._on_error)

    @Slot(str, str)
    def _on_state_changed(self, command_id: str, state: str) -> None:
        if command_id != self.command_id:
            return
        self._is_running = state == "Running"
        self.status_label.setText(state)
        color_map = {
            "Running": STATUS_RUNNING,
            "Stopped": STATUS_STOPPED,
            "Failed": STATUS_FAILED,
        }
        self.status_label.setStyleSheet(
            f"font-size: 13px; font-weight: bold; color: {color_map.get(state, TEXT_SECONDARY)};"
        )
        self.stop_btn.setEnabled(self._is_running)
        self.update_title()

    @Slot(str, str)
    def _on_output(self, command_id: str, text: str) -> None:
        if command_id != self.command_id:
            return
        self._append(text)

    @Slot(str, str)
    def _on_error(self, command_id: str, text: str) -> None:
        if command_id != self.command_id:
            return
        self._append(text, error=True)

    def _append(self, text: str, error: bool = False) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        for line in text.rstrip().splitlines():
            prefix = f"[{ts}]"
            if error:
                self.output.append(f'<span style="color:#f85149">{prefix} {line}</span>')
            else:
                self.output.append(f"{prefix} {line}")
        sb = self.output.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _stop_process(self) -> None:
        self.process_service.stop(int(self.command_id))

    def _clear_output(self) -> None:
        self.output.clear()

    def update_title(self) -> None:
        prefix = "▶" if self._is_running else "⏹"
        self.setWindowTitle(f"{prefix} Logs: {self.command_name}")

    def closeEvent(self, event) -> None:
        self.disconnect_signals()
        event.accept()
