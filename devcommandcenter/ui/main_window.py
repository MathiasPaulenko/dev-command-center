from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devcommandcenter.database.connection import SessionLocal, init_db
from devcommandcenter.database.models import Command
from devcommandcenter.services.command_service import CommandService
from devcommandcenter.services.process_service import ProcessService
from devcommandcenter.ui.command_dialog import CommandDialog


class CommandCard(QWidget):
    def __init__(self, command: Command, parent=None) -> None:
        super().__init__(parent)
        self.command_id = command.id
        self.command_obj = command
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        info_layout = QVBoxLayout()
        self.name_label = QLabel(f"<b>{self.command_obj.name}</b>")
        self.name_label.setStyleSheet("font-size: 14px;")
        self.desc_label = QLabel(self.command_obj.description or "")
        self.desc_label.setStyleSheet("color: #888; font-size: 12px;")
        self.status_label = QLabel("Stopped")
        self.status_label.setStyleSheet(
            "color: #888; font-size: 11px; font-weight: bold;"
        )
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.desc_label)
        info_layout.addWidget(self.status_label)
        layout.addLayout(info_layout, stretch=1)

        self.run_btn = QPushButton("Run")
        self.run_btn.setFixedWidth(60)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setFixedWidth(60)
        self.stop_btn.setEnabled(False)
        self.logs_btn = QPushButton("Logs")
        self.logs_btn.setFixedWidth(60)
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setFixedWidth(60)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setFixedWidth(60)

        layout.addWidget(self.run_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.logs_btn)
        layout.addWidget(self.edit_btn)
        layout.addWidget(self.delete_btn)

        self.setStyleSheet(
            """
            QWidget {
                background-color: #2b2b2b;
                border-radius: 8px;
            }
            QLabel {
                background: transparent;
            }
            QPushButton {
                background-color: #3c3c3c;
                color: #ddd;
                border: none;
                border-radius: 4px;
                padding: 6px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QPushButton:pressed {
                background-color: #606060;
            }
            QPushButton:disabled {
                color: #666;
            }
        """
        )

    def update_status(self, state: str) -> None:
        self.status_label.setText(state)
        color_map = {
            "Running": "#4caf50",
            "Stopped": "#888",
            "Failed": "#f44336",
        }
        self.status_label.setStyleSheet(
            f"color: {color_map.get(state, '#888')}; font-size: 11px; font-weight: bold;"
        )
        self.run_btn.setEnabled(state != "Running")
        self.stop_btn.setEnabled(state == "Running")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DevCommandCenter")
        self.resize(900, 600)
        self.process_service = ProcessService()
        self.process_service.stateChanged.connect(self.on_state_changed)
        self.process_service.outputReady.connect(self.on_output_ready)
        self.process_service.errorReady.connect(self.on_error_ready)
        self.process_service.logReady.connect(self.on_log_ready)
        self._command_names: dict[int, str] = {}
        self._running_ids: set[int] = set()
        self.setup_ui()
        self.load_commands()
        self._auto_run_commands()

    def setup_ui(self) -> None:
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        import_action = file_menu.addAction("Import JSON")
        export_action = file_menu.addAction("Export JSON")
        file_menu.addSeparator()
        exit_action = file_menu.addAction("Exit")
        help_menu = menu_bar.addMenu("Help")
        about_action = help_menu.addAction("About")

        import_action.triggered.connect(self.import_commands)
        export_action.triggered.connect(self.export_commands)
        exit_action.triggered.connect(self.close)
        about_action.triggered.connect(self.show_about)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        header = QHBoxLayout()
        header.addWidget(QLabel("<h2>Commands</h2>"))
        header.addStretch()
        self.add_btn = QPushButton("+ New Command")
        header.addWidget(self.add_btn)
        left_layout.addLayout(header)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search commands...")
        self.search_box.textChanged.connect(self.filter_commands)
        left_layout.addWidget(self.search_box)

        self.list_widget = QListWidget()
        self.list_widget.setSpacing(8)
        self.list_widget.setStyleSheet(
            """
            QListWidget {
                background-color: #1e1e1e;
                border: none;
            }
            QListWidget::item {
                background: transparent;
                padding: 4px;
            }
        """
        )
        left_layout.addWidget(self.list_widget, stretch=1)
        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)
        self.logs_area = QTextEdit()
        self.logs_area.setReadOnly(True)
        self.logs_area.setStyleSheet(
            """
            QTextEdit {
                background-color: #1e1e1e;
                color: #ccc;
                font-family: Consolas, monospace;
                font-size: 12px;
                border: 1px solid #333;
                border-radius: 6px;
            }
        """
        )
        log_header = QHBoxLayout()
        log_header.addWidget(QLabel("<h2>Logs</h2>"))
        log_header.addStretch()
        self.clear_logs_btn = QPushButton("Clear")
        self.clear_logs_btn.setFixedWidth(60)
        self.clear_logs_btn.clicked.connect(self.logs_area.clear)
        log_header.addWidget(self.clear_logs_btn)
        right_layout.addLayout(log_header)
        right_layout.addWidget(self.logs_area)
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 300])

        self.setStyleSheet("background-color: #1e1e1e; color: #ddd;")
        self.add_btn.clicked.connect(self.open_create_dialog)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status_bar()

        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)

    def load_commands(self) -> None:
        self.list_widget.clear()
        self._command_names.clear()
        self._all_commands: list[Command] = []
        session = SessionLocal()
        try:
            service = CommandService(session)
            commands = service.get_all()
            self._all_commands = commands
            for cmd in commands:
                self._command_names[cmd.id] = cmd.name
                self.add_command_card(cmd)
        finally:
            session.close()

    def filter_commands(self, text: str) -> None:
        text = text.lower()
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            card = self.list_widget.itemWidget(item)
            if card:
                match = (
                    text in card.command_obj.name.lower()
                    or (card.command_obj.description and text in card.command_obj.description.lower())
                    or any(text in t.lower() for t in (card.command_obj.tags or []))
                )
                item.setHidden(not match)

    def add_command_card(self, command: Command) -> None:
        item = QListWidgetItem()
        card = CommandCard(command)
        card.run_btn.clicked.connect(lambda _, c=command: self.run_command(c))
        card.stop_btn.clicked.connect(lambda _, c=command: self.stop_command(c))
        card.logs_btn.clicked.connect(lambda _, c=command: self.show_logs_for_command(c))
        card.edit_btn.clicked.connect(lambda _, c=command: self.edit_command(c))
        card.delete_btn.clicked.connect(lambda _, c=command: self.delete_command(c))
        current_state = self.process_service.get_state(command.id)
        card.update_status(current_state)
        card.adjustSize()
        item.setSizeHint(card.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, card)

    def run_command(self, command: Command) -> None:
        args = command.arguments or []
        env = command.env_vars or {}
        ok = self.process_service.start(
            command.id, command.command, args,
            command.working_directory or "", env
        )
        if ok:
            self._running_ids.add(command.id)
            self._update_status_bar()
            self._append_log(f"[Run] {command.name}")
        else:
            self._append_log(f"[Already running] {command.name}")

    def stop_command(self, command: Command) -> None:
        self.process_service.stop(command.id)
        self._running_ids.discard(command.id)
        self._update_status_bar()
        self._append_log(f"[Stop] {command.name}")

    @Slot(str, str)
    def on_state_changed(self, command_id: str, state: str) -> None:
        cid = int(command_id)
        self.update_card_status(cid, state)
        if state == "Running":
            self._running_ids.add(cid)
        elif state in ("Stopped", "Failed"):
            self._running_ids.discard(cid)
        self._update_status_bar()

    @Slot(str, str)
    def on_output_ready(self, command_id: str, text: str) -> None:
        name = self._command_names.get(int(command_id), f"#{command_id}")
        for line in text.rstrip().splitlines():
            self._append_log(f"[{name}] {line}")

    @Slot(str, str)
    def on_error_ready(self, command_id: str, text: str) -> None:
        name = self._command_names.get(int(command_id), f"#{command_id}")
        for line in text.rstrip().splitlines():
            self._append_log(f'<span style="color:#f44336">[{name}] {line}</span>')

    def _append_log(self, message: str) -> None:
        from datetime import datetime
        ts = datetime.now().strftime("%H:%M:%S")
        self.logs_area.append(f"[{ts}] {message}")
        sb = self.logs_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _update_status_bar(self) -> None:
        count = len(self._running_ids)
        self.status_bar.showMessage(f"Running: {count} process(es)")

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        card = self.list_widget.itemWidget(item)
        if card:
            self.run_command(card.command_obj)

    @Slot(str, str, str, int)
    def on_log_ready(self, command_id: str, stdout: str, stderr: str, exit_code: int) -> None:
        from devcommandcenter.services.execution_log_service import ExecutionLogService
        session = SessionLocal()
        try:
            service = ExecutionLogService(session)
            service.create({
                "command_id": int(command_id),
                "output": stdout or None,
                "error": stderr or None,
                "exit_code": exit_code,
            })
        finally:
            session.close()

    def update_card_status(self, command_id: int, state: str) -> None:
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            card = self.list_widget.itemWidget(item)
            if card and card.command_id == command_id:
                card.update_status(state)
                break

    def open_create_dialog(self) -> None:
        dialog = CommandDialog(self)
        if dialog.exec() == QDialog.Accepted:
            session = SessionLocal()
            try:
                service = CommandService(session)
                service.create(dialog.get_data())
                self.load_commands()
            finally:
                session.close()

    def edit_command(self, command: Command) -> None:
        dialog = CommandDialog(self, command=command)
        if dialog.exec() == QDialog.Accepted:
            session = SessionLocal()
            try:
                service = CommandService(session)
                service.update(command.id, dialog.get_data())
                self.load_commands()
            finally:
                session.close()

    def show_logs_for_command(self, command: Command) -> None:
        from devcommandcenter.services.execution_log_service import ExecutionLogService
        session = SessionLocal()
        try:
            service = ExecutionLogService(session)
            logs = service.get_by_command_id(command.id)
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Logs: {command.name}")
            dialog.resize(600, 400)
            layout = QVBoxLayout(dialog)
            header = QHBoxLayout()
            header.addWidget(QLabel("<b>Execution History</b>"))
            header.addStretch()
            copy_btn = QPushButton("Copy")
            copy_btn.setFixedWidth(60)
            header.addWidget(copy_btn)
            layout.addLayout(header)
            text = QTextEdit()
            text.setReadOnly(True)
            text.setStyleSheet(
                """
                QTextEdit {
                    background-color: #1e1e1e;
                    color: #ccc;
                    font-family: Consolas, monospace;
                    font-size: 12px;
                }
            """
            )
            copy_btn.clicked.connect(lambda: QApplication.clipboard().setText(text.toPlainText()))
            if logs:
                lines = []
                for log in logs:
                    lines.append(f"--- {log.started_at} | exit={log.exit_code} ---")
                    if log.output:
                        lines.append(log.output)
                    if log.error:
                        lines.append(f"[stderr]\n{log.error}")
                text.setPlainText("\n".join(lines))
            else:
                text.setPlainText("No execution logs yet.")
            layout.addWidget(text)
            dialog.exec()
        finally:
            session.close()

    def _auto_run_commands(self) -> None:
        for cmd in getattr(self, "_all_commands", []):
            if cmd.auto_run:
                self.run_command(cmd)

    def delete_command(self, command: Command) -> None:
        reply = QMessageBox.question(
            self, "Confirm", f"Delete '{command.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.process_service.stop(command.id)
            session = SessionLocal()
            try:
                service = CommandService(session)
                if service.delete(command.id):
                    self.load_commands()
            finally:
                session.close()

    def import_commands(self) -> None:
        import json
        path, _ = QFileDialog.getOpenFileName(self, "Import Commands", "", "JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            session = SessionLocal()
            try:
                service = CommandService(session)
                for item in data:
                    item.pop("id", None)
                    item.pop("created_at", None)
                    item.pop("updated_at", None)
                    service.create(item)
                self.load_commands()
                QMessageBox.information(self, "Import", f"Imported {len(data)} commands.")
            finally:
                session.close()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    def export_commands(self) -> None:
        import json
        path, _ = QFileDialog.getSaveFileName(self, "Export Commands", "commands.json", "JSON (*.json)")
        if not path:
            return
        try:
            session = SessionLocal()
            try:
                service = CommandService(session)
                commands = service.get_all()
                data = []
                for cmd in commands:
                    data.append({
                        "id": cmd.id,
                        "name": cmd.name,
                        "description": cmd.description,
                        "working_directory": cmd.working_directory,
                        "command": cmd.command,
                        "arguments": cmd.arguments,
                        "env_vars": cmd.env_vars,
                        "auto_run": cmd.auto_run,
                        "tags": cmd.tags,
                    })
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                QMessageBox.information(self, "Export", f"Exported {len(data)} commands.")
            finally:
                session.close()
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def show_about(self) -> None:
        from devcommandcenter.config import APP_NAME, APP_VERSION
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h2>{APP_NAME}</h2>"
            f"<p>Version {APP_VERSION}</p>"
            "<p>Desktop app for managing and running development commands.</p>",
        )

    def closeEvent(self, event) -> None:
        self.process_service.stop_all()
        event.accept()
