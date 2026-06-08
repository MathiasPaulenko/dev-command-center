import json
from datetime import datetime

from PySide6.QtCore import QCoreApplication, Qt, Slot
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

from devcommandcenter.config import APP_NAME, APP_VERSION
from devcommandcenter.database.connection import SessionLocal, init_db
from devcommandcenter.database.models import Command
from devcommandcenter.services.command_service import CommandService
from devcommandcenter.services.execution_log_service import ExecutionLogService
from devcommandcenter.services.process_service import ProcessService
from devcommandcenter.ui.command_dialog import CommandDialog
from devcommandcenter.ui.theme import (
    ACCENT_DANGER,
    ACCENT_DANGER_HOVER,
    ACCENT_PRIMARY,
    ACCENT_PRIMARY_HOVER,
    ACCENT_SUCCESS,
    APP_STYLESHEET,
    BG_ELEVATED,
    BG_INPUT,
    BG_PRIMARY,
    BORDER,
    BORDER_HOVER,
    DIALOG_STYLESHEET,
    STATUS_FAILED,
    STATUS_RUNNING,
    STATUS_STOPPED,
    TEXT_DISABLED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    card_stylesheet,
    status_badge_stylesheet,
)


class CommandCard(QWidget):
    def __init__(self, command: Command, parent=None) -> None:
        super().__init__(parent)
        self.command_id = command.id
        self.command_obj = command
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(14)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(4)

        top_row = QHBoxLayout()
        self.name_label = QLabel(f"<b>{self.command_obj.name}</b>")
        self.name_label.setStyleSheet(
            f"font-size: 15px; color: {TEXT_PRIMARY}; background: transparent; border: none;"
        )
        self.status_badge = QLabel("Stopped")
        self.status_badge.setStyleSheet(status_badge_stylesheet(STATUS_STOPPED))
        top_row.addWidget(self.name_label)
        top_row.addStretch()
        top_row.addWidget(self.status_badge)
        info_layout.addLayout(top_row)

        desc_text = self.command_obj.description or "No description"
        self.desc_label = QLabel(desc_text)
        self.desc_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 12px; background: transparent; border: none;"
        )
        self.desc_label.setWordWrap(True)
        info_layout.addWidget(self.desc_label)

        tags_text = ", ".join(self.command_obj.tags or [])
        self.tags_label = QLabel(tags_text)
        self.tags_label.setStyleSheet(
            f"color: {TEXT_DISABLED}; font-size: 11px; background: transparent; border: none;"
        )
        info_layout.addWidget(self.tags_label)

        layout.addLayout(info_layout, stretch=1)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(6)

        self.run_btn = QPushButton("▶ Run")
        self.run_btn.setFixedWidth(70)
        self.run_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ACCENT_SUCCESS};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {ACCENT_PRIMARY_HOVER}; }}
            QPushButton:disabled {{ background-color: {BG_INPUT}; color: {TEXT_DISABLED}; }}
        """
        )

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setFixedWidth(70)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ACCENT_DANGER};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 5px 10px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {ACCENT_DANGER_HOVER}; }}
            QPushButton:disabled {{ background-color: {BG_INPUT}; color: {TEXT_DISABLED}; }}
        """
        )

        self.logs_btn = QPushButton("Logs")
        self.logs_btn.setFixedWidth(55)
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setFixedWidth(55)
        self.delete_btn = QPushButton("Del")
        self.delete_btn.setFixedWidth(45)

        btn_layout.addWidget(self.run_btn)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addWidget(self.logs_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        layout.addLayout(btn_layout)

        self.setStyleSheet(card_stylesheet())

    def update_status(self, state: str) -> None:
        self.status_badge.setText(state)
        color_map = {
            "Running": STATUS_RUNNING,
            "Stopped": STATUS_STOPPED,
            "Failed": STATUS_FAILED,
        }
        self.status_badge.setStyleSheet(
            status_badge_stylesheet(color_map.get(state, STATUS_STOPPED))
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
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(12)

        header = QHBoxLayout()
        header_label = QLabel("Commands")
        header_label.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {TEXT_PRIMARY};"
        )
        header.addWidget(header_label)
        header.addStretch()
        self.add_btn = QPushButton("+ New Command")
        self.add_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ACCENT_PRIMARY};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {ACCENT_PRIMARY_HOVER}; }}
        """
        )
        header.addWidget(self.add_btn)
        left_layout.addLayout(header)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search commands...")
        self.search_box.textChanged.connect(self.filter_commands)
        left_layout.addWidget(self.search_box)

        self.list_widget = QListWidget()
        self.list_widget.setSpacing(8)
        left_layout.addWidget(self.list_widget, stretch=1)
        splitter.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)

        self.logs_area = QTextEdit()
        self.logs_area.setReadOnly(True)

        log_header = QHBoxLayout()
        log_label = QLabel("Logs")
        log_label.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {TEXT_PRIMARY};"
        )
        log_header.addWidget(log_label)
        log_header.addStretch()
        self.clear_logs_btn = QPushButton("Clear")
        self.clear_logs_btn.setFixedWidth(60)
        self.clear_logs_btn.clicked.connect(self.logs_area.clear)
        log_header.addWidget(self.clear_logs_btn)
        right_layout.addLayout(log_header)
        right_layout.addWidget(self.logs_area)
        splitter.addWidget(right_widget)
        splitter.setSizes([600, 300])

        self.setStyleSheet(APP_STYLESHEET)
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
        session = SessionLocal()
        try:
            service = ExecutionLogService(session)
            logs = service.get_by_command_id(command.id)
            dialog = QDialog(self)
            dialog.setStyleSheet(DIALOG_STYLESHEET)
            dialog.setWindowTitle(f"Logs: {command.name}")
            dialog.resize(600, 400)
            layout = QVBoxLayout(dialog)
            layout.setContentsMargins(16, 16, 16, 16)
            layout.setSpacing(12)

            header = QHBoxLayout()
            header_label = QLabel("Execution History")
            header_label.setStyleSheet(
                f"font-size: 15px; font-weight: bold; color: {TEXT_PRIMARY};"
            )
            header.addWidget(header_label)
            header.addStretch()
            copy_btn = QPushButton("Copy")
            copy_btn.setFixedWidth(60)
            header.addWidget(copy_btn)
            layout.addLayout(header)
            text = QTextEdit()
            text.setReadOnly(True)
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
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            f"<h2>{APP_NAME}</h2>"
            f"<p>Version {APP_VERSION}</p>"
            "<p>Desktop app for managing and running development commands.</p>",
        )

    def closeEvent(self, event) -> None:
        self.process_service.stop_all()
        for _ in range(20):
            QCoreApplication.processEvents()
        event.accept()
