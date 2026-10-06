"""Execution history dialog — per-command list of past runs."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devcommandcenter.database.connection import SessionLocal
from devcommandcenter.database.models import Command, ExecutionLog
from devcommandcenter.services.execution_log_service import ExecutionLogService
from devcommandcenter.ui.theme import (
    BG_BASE,
    BG_CARD,
    BG_CODE,
    BG_ELEVATED,
    BG_INPUT,
    BORDER,
    GREEN,
    RED,
    RED_FILL,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class ExecutionHistoryDialog(QDialog):
    historyCleared = Signal(int)

    def __init__(self, command: Command, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.command_id = command.id
        self.setWindowTitle(f"Execution History: {command.name}")
        self.resize(700, 500)
        self.setup_ui()
        self._load_history(command.id)

    def setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        header = QWidget()
        header.setFixedHeight(56)
        header.setStyleSheet(
            f"background-color: {BG_CARD}; border-bottom: 1px solid {BORDER};"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        title = QLabel(self.windowTitle())
        title.setStyleSheet(
            f"font-size: 16px; font-weight: 700; color: {TEXT_PRIMARY};"
            f"background: transparent; border: none;"
        )
        header_layout.addWidget(title)
        header_layout.addStretch()
        root.addWidget(header)

        body = QWidget()
        body.setStyleSheet(f"background-color: {BG_BASE};")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 16, 20, 16)
        body_layout.setSpacing(12)

        self.list_widget = QListWidget()
        self.list_widget.setStyleSheet(
            f"QListWidget {{ background-color: {BG_INPUT}; color: {TEXT_PRIMARY};"
            f"border: 1px solid {BORDER}; border-radius: 8px; }}"
            f"QListWidget::item {{ padding: 10px; border-bottom: 1px solid {BORDER}; }}"
            f"QListWidget::item:selected {{ background-color: {BG_ELEVATED}; }}"
        )
        self.list_widget.itemClicked.connect(self._on_item_clicked)
        body_layout.addWidget(self.list_widget)

        self.detail = QTextEdit()
        self.detail.setReadOnly(True)
        self.detail.setMaximumHeight(160)
        self.detail.setStyleSheet(
            f"QTextEdit {{ background-color: {BG_CODE}; color: {TEXT_PRIMARY};"
            f"border: 1px solid {BORDER}; border-radius: 8px; padding: 12px;"
            f"font-family: 'JetBrains Mono','Consolas',monospace; font-size: 12px; }}"
        )
        body_layout.addWidget(self.detail)

        root.addWidget(body, stretch=1)

        footer = QWidget()
        footer.setFixedHeight(64)
        footer.setStyleSheet(
            f"background-color: {BG_CARD}; border-top: 1px solid {BORDER};"
        )
        footer_layout = QHBoxLayout(footer)
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_layout.setContentsMargins(20, 0, 20, 0)

        clear_btn = QPushButton("Clear History")
        clear_btn.setMinimumHeight(36)
        clear_btn.setStyleSheet(
            f"QPushButton {{ background-color: {BG_ELEVATED}; color: {RED};"
            f"border: 1px solid {BORDER}; border-radius: 8px;"
            f"padding: 7px 16px; font-size: 12px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {RED_FILL}; color: #ffffff; border-color: {RED_FILL}; }}"
        )
        clear_btn.clicked.connect(self._clear_history)
        footer_layout.addWidget(clear_btn)

        footer_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(36)
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        root.addWidget(footer)

    def _clear_history(self) -> None:
        reply = QMessageBox.question(
            self,
            "Confirm Clear",
            "Delete all execution history for this command?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        session = SessionLocal()
        try:
            ExecutionLogService(session).delete_by_command_id(self.command_id)
        finally:
            session.close()
        self.list_widget.clear()
        self.detail.clear()
        self.list_widget.addItem("No executions recorded yet.")
        self.historyCleared.emit(self.command_id)

    def _load_history(self, command_id: int) -> None:
        session = SessionLocal()
        try:
            logs = ExecutionLogService(session).get_by_command_id(command_id)
        finally:
            session.close()

        if not logs:
            self.list_widget.addItem("No executions recorded yet.")
            return

        for log in logs:
            started = log.started_at.strftime("%Y-%m-%d %H:%M:%S") if log.started_at else "?"
            if log.exit_code == 0:
                status = "Success"
                status_color = GREEN
            elif log.exit_code is None:
                status = "Unknown"
                status_color = TEXT_SECONDARY
            else:
                status = f"Failed (exit {log.exit_code})"
                status_color = RED
            item = QListWidgetItem(f"{started}  —  {status}")
            item.setForeground(QColor(status_color))
            item.setData(Qt.ItemDataRole.UserRole, log)
            self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)
            self._on_item_clicked(self.list_widget.item(0))

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        log = item.data(Qt.ItemDataRole.UserRole)
        if not isinstance(log, ExecutionLog):
            return
        parts: list[str] = []
        started = log.started_at.strftime("%Y-%m-%d %H:%M:%S") if log.started_at else "?"
        finished = log.finished_at.strftime("%Y-%m-%d %H:%M:%S") if log.finished_at else "?"
        parts.append(f"Started:  {started}")
        parts.append(f"Finished: {finished}")
        parts.append(f"Exit code: {log.exit_code}")
        parts.append("")
        if log.output:
            parts.append("STDOUT:")
            parts.append(log.output)
        if log.error:
            parts.append("STDERR:")
            parts.append(log.error)
        if not log.output and not log.error:
            parts.append("(no output captured)")
        self.detail.setPlainText("\n".join(parts))
