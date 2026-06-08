import json

from PySide6.QtCore import QCoreApplication, Qt, Slot
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStatusBar,
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
from devcommandcenter.ui.log_window import LogWindow
from devcommandcenter.ui.theme import (
    ACCENT_DANGER,
    ACCENT_DANGER_HOVER,
    ACCENT_PRIMARY,
    ACCENT_PRIMARY_HOVER,
    ACCENT_SUCCESS,
    APP_STYLESHEET,
    BG_CODE,
    BG_ELEVATED,
    BG_INPUT,
    BG_PRIMARY,
    BG_SURFACE,
    BORDER,
    BORDER_HOVER,
    STATUS_FAILED,
    STATUS_RUNNING,
    STATUS_STOPPED,
    TEXT_DISABLED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    card_stylesheet,
    status_badge_stylesheet,
    tag_chip_stylesheet,
)


class CommandCard(QWidget):
    def __init__(self, command: Command, parent=None) -> None:
        super().__init__(parent)
        self.command_id = command.id
        self.command_obj = command
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        # ── Top: status dot + name + badge ────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(10)

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet(
            f"font-size: 14px; color: {STATUS_STOPPED}; background: transparent; border: none;"
        )
        self.name_label = QLabel(f"{self.command_obj.name}")
        self.name_label.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {TEXT_PRIMARY}; background: transparent; border: none;"
        )
        self.name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.status_badge = QLabel("Stopped")
        self.status_badge.setStyleSheet(status_badge_stylesheet(STATUS_STOPPED))
        top_row.addWidget(self.status_dot)
        top_row.addWidget(self.name_label)
        top_row.addStretch()
        top_row.addWidget(self.status_badge)
        layout.addLayout(top_row)

        # ── Description ───────────────────────────────────────
        desc_text = self.command_obj.description or "No description"
        self.desc_label = QLabel(desc_text)
        self.desc_label.setStyleSheet(
            f"color: {TEXT_SECONDARY}; font-size: 13px; background: transparent; border: none;"
        )
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label)

        # ── Command chip ──────────────────────────────────────
        cmd_text = self.command_obj.command or ""
        self.cmd_chip = QLabel(f"$ {cmd_text}")
        self.cmd_chip.setStyleSheet(
            f"color: {ACCENT_SUCCESS}; background-color: {BG_CODE};"
            f"border: 1px solid {BORDER}; border-radius: 6px;"
            f"padding: 6px 12px; font-family: 'JetBrains Mono','Fira Code','Consolas',monospace;"
            f"font-size: 12px;"
        )
        self.cmd_chip.setWordWrap(True)
        layout.addWidget(self.cmd_chip)

        # ── Tags ──────────────────────────────────────────────
        tags = self.command_obj.tags or []
        if tags:
            tags_row = QHBoxLayout()
            tags_row.setSpacing(6)
            tags_row.setContentsMargins(0, 0, 0, 0)
            for tag in tags[:4]:
                chip = QLabel(f"#{tag}")
                chip.setStyleSheet(tag_chip_stylesheet())
                tags_row.addWidget(chip)
            tags_row.addStretch()
            layout.addLayout(tags_row)

        layout.addStretch()

        # ── Separator ─────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"background-color: {BORDER}; border: none; max-height: 1px;")
        layout.addWidget(sep)

        # ── Primary actions ───────────────────────────────────
        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        self.run_btn = QPushButton("▶  Run")
        self.run_btn.setMinimumHeight(42)
        self.run_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.run_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ACCENT_SUCCESS}22;
                color: {ACCENT_SUCCESS};
                border: 1px solid {ACCENT_SUCCESS}44;
                border-radius: 10px;
                padding: 10px 0;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_SUCCESS};
                color: {BG_PRIMARY};
                border-color: {ACCENT_SUCCESS};
            }}
            QPushButton:disabled {{
                background-color: {BG_INPUT};
                color: {TEXT_DISABLED};
                border-color: {BORDER};
            }}
        """
        )

        self.stop_btn = QPushButton("⏹  Stop")
        self.stop_btn.setMinimumHeight(42)
        self.stop_btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ACCENT_DANGER}22;
                color: {ACCENT_DANGER};
                border: 1px solid {ACCENT_DANGER}44;
                border-radius: 10px;
                padding: 10px 0;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {ACCENT_DANGER};
                color: {BG_PRIMARY};
                border-color: {ACCENT_DANGER};
            }}
            QPushButton:disabled {{
                background-color: {BG_INPUT};
                color: {TEXT_DISABLED};
                border-color: {BORDER};
            }}
        """
        )

        action_row.addWidget(self.run_btn)
        action_row.addWidget(self.stop_btn)
        layout.addLayout(action_row)

        # ── Secondary actions ─────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        self.logs_btn = QPushButton("📋 Logs")
        self.logs_btn.setMinimumHeight(34)
        self.edit_btn = QPushButton("✏ Edit")
        self.edit_btn.setMinimumHeight(34)
        self.delete_btn = QPushButton("🗑 Delete")
        self.delete_btn.setMinimumHeight(34)
        self.delete_btn.setStyleSheet(
            f"QPushButton {{ color: {ACCENT_DANGER}; }}"
            f"QPushButton:hover {{ color: {BG_PRIMARY}; background-color: {ACCENT_DANGER}; border-color: {ACCENT_DANGER}; }}"
        )
        for b in (self.logs_btn, self.edit_btn, self.delete_btn):
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        btn_row.addWidget(self.logs_btn)
        btn_row.addWidget(self.edit_btn)
        btn_row.addWidget(self.delete_btn)
        layout.addLayout(btn_row)

        self.setMinimumHeight(300)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        self.setStyleSheet(card_stylesheet())

    def update_status(self, state: str) -> None:
        self.status_badge.setText(state)
        color_map = {
            "Running": STATUS_RUNNING,
            "Stopped": STATUS_STOPPED,
            "Failed": STATUS_FAILED,
        }
        color = color_map.get(state, STATUS_STOPPED)
        self.status_badge.setStyleSheet(status_badge_stylesheet(color))
        self.status_dot.setStyleSheet(
            f"font-size: 14px; color: {color}; background: transparent; border: none;"
        )
        self.run_btn.setEnabled(state != "Running")
        self.stop_btn.setEnabled(state == "Running")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DevCommandCenter")
        self.resize(1400, 900)
        self.process_service = ProcessService()
        self.process_service.stateChanged.connect(self.on_state_changed)
        self.process_service.logReady.connect(self.on_log_ready)
        self._command_names: dict[int, str] = {}
        self._running_ids: set[int] = set()
        self._log_windows: dict[int, LogWindow] = {}
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
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Top navbar ─────────────────────────────────────────
        navbar = QWidget()
        navbar.setFixedHeight(70)
        navbar.setStyleSheet(
            f"background-color: {BG_SURFACE}; border-bottom: 1px solid {BORDER};"
        )
        navbar_layout = QHBoxLayout(navbar)
        navbar_layout.setContentsMargins(28, 0, 28, 0)
        navbar_layout.setSpacing(16)

        brand_icon = QLabel("⚡")
        brand_icon.setStyleSheet(
            f"font-size: 28px; background: transparent; border: none; color: {ACCENT_PRIMARY};"
        )
        brand_col = QVBoxLayout()
        brand_col.setSpacing(0)
        brand_title = QLabel("DevCommandCenter")
        brand_title.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {TEXT_PRIMARY}; background: transparent; border: none;"
        )
        brand_sub = QLabel(f"v{APP_VERSION}  •  command runner")
        brand_sub.setStyleSheet(
            f"font-size: 11px; color: {TEXT_DISABLED}; background: transparent; border: none;"
        )
        brand_col.addWidget(brand_title)
        brand_col.addWidget(brand_sub)
        navbar_layout.addWidget(brand_icon)
        navbar_layout.addLayout(brand_col)
        navbar_layout.addStretch()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Search commands...")
        self.search_box.setFixedWidth(280)
        self.search_box.setFixedHeight(38)
        self.search_box.textChanged.connect(self.filter_commands)
        navbar_layout.addWidget(self.search_box)

        self.add_btn = QPushButton("+ New Command")
        self.add_btn.setFixedHeight(38)
        self.add_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {ACCENT_PRIMARY};
                color: {BG_PRIMARY};
                border: none;
                border-radius: 10px;
                padding: 0 22px;
                font-size: 14px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background-color: {ACCENT_PRIMARY_HOVER}; }}
        """
        )
        navbar_layout.addWidget(self.add_btn)
        root.addWidget(navbar)

        # ── Content area ────────────────────────────────────
        content = QWidget()
        content.setStyleSheet(f"background-color: {BG_PRIMARY};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 24, 28, 16)
        content_layout.setSpacing(16)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(20)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_area.setWidget(self.grid_container)
        content_layout.addWidget(self.scroll_area, stretch=1)
        root.addWidget(content, stretch=1)

        self.setStyleSheet(APP_STYLESHEET)
        self.add_btn.clicked.connect(self.open_create_dialog)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status_bar()

    def load_commands(self) -> None:
        # Clear existing cards from grid
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._command_names.clear()
        self._all_commands: list[Command] = []
        self._cards: dict[int, CommandCard] = {}
        session = SessionLocal()
        try:
            service = CommandService(session)
            commands = service.get_all()
            self._all_commands = commands
            for idx, cmd in enumerate(commands):
                self._command_names[cmd.id] = cmd.name
                self.add_command_card(cmd, idx)
        finally:
            session.close()

    def filter_commands(self, text: str) -> None:
        text = text.lower()
        for card in self._cards.values():
            match = (
                text in card.command_obj.name.lower()
                or (card.command_obj.description and text in card.command_obj.description.lower())
                or any(text in t.lower() for t in (card.command_obj.tags or []))
            )
            card.setVisible(match)

    def add_command_card(self, command: Command, index: int) -> None:
        card = CommandCard(command)
        card.run_btn.clicked.connect(lambda _, c=command: self.run_command(c))
        card.stop_btn.clicked.connect(lambda _, c=command: self.stop_command(c))
        card.logs_btn.clicked.connect(lambda _, c=command: self.show_logs_for_command(c))
        card.edit_btn.clicked.connect(lambda _, c=command: self.edit_command(c))
        card.delete_btn.clicked.connect(lambda _, c=command: self.delete_command(c))
        card.mouseDoubleClickEvent = lambda ev, c=command: self.run_command(c)
        current_state = self.process_service.get_state(command.id)
        card.update_status(current_state)
        row = index // 3
        col = index % 3
        self.grid_layout.addWidget(card, row, col)
        self._cards[command.id] = card

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
        else:
            QMessageBox.information(self, "Info", f"'{command.name}' is already running.")

    def stop_command(self, command: Command) -> None:
        self.process_service.stop(command.id)
        self._running_ids.discard(command.id)
        self._update_status_bar()

    @Slot(str, str)
    def on_state_changed(self, command_id: str, state: str) -> None:
        cid = int(command_id)
        self.update_card_status(cid, state)
        if state == "Running":
            self._running_ids.add(cid)
        elif state in ("Stopped", "Failed"):
            self._running_ids.discard(cid)
        self._update_status_bar()

    def _update_status_bar(self) -> None:
        count = len(self._running_ids)
        self.status_bar.showMessage(f"Running: {count} process(es)")

    def _on_item_double_clicked(self, item) -> None:
        pass

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
        card = self._cards.get(command_id)
        if card:
            card.update_status(state)

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
        if command.id in self._log_windows:
            win = self._log_windows[command.id]
            win.raise_()
            win.activateWindow()
            return

        win = LogWindow(command.id, command.name, self.process_service, self)
        win.finished.connect(lambda: self._log_windows.pop(command.id, None))
        self._log_windows[command.id] = win
        win.show()

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
