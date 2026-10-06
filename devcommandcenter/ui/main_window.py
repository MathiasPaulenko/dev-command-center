from __future__ import annotations

import json
import time
from datetime import datetime

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
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from devcommandcenter.config import APP_VERSION
from devcommandcenter.database.connection import SessionLocal
from devcommandcenter.database.models import Command
from devcommandcenter.services.command_service import CommandService
from devcommandcenter.services.execution_log_service import ExecutionLogService
from devcommandcenter.services.process_service import ProcessService
from devcommandcenter.ui.about_dialog import AboutDialog
from devcommandcenter.ui.command_card import CARD_WIDTH, CommandCard
from devcommandcenter.ui.command_dialog import CommandDialog
from devcommandcenter.ui.history_dialog import ExecutionHistoryDialog
from devcommandcenter.ui.log_window import LogWindow
from devcommandcenter.ui.theme import (
    ACCENT_FILL,
    ACCENT_HOVER,
    APP_STYLESHEET,
    BG_BASE,
    BG_CARD,
    BG_ELEVATED,
    BG_SIDEBAR,
    BORDER,
    GREEN,
    RED,
    TEXT_DISABLED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    sidebar_btn_stylesheet,
)

GRID_SPACING = 20


def _now() -> datetime:
    return datetime.now()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DevCommandCenter")
        self.resize(1440, 900)
        self.process_service = ProcessService()
        self.process_service.stateChanged.connect(self.on_state_changed)
        self.process_service.logReady.connect(self.on_log_ready)
        self._running_ids: set[int] = set()
        self._log_windows: dict[int, LogWindow] = {}
        self._cards: dict[int, CommandCard] = {}
        self._all_commands: list[Command] = []
        self._filter_state: str = "All"
        self._filter_text: str = ""
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
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(
            f"background-color: {BG_SIDEBAR};"
            f"border-right: 1px solid {BORDER};"
        )
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(16, 24, 16, 20)
        sb_layout.setSpacing(4)

        brand = QLabel("DevCommandCenter")
        brand.setWordWrap(False)
        brand.setStyleSheet(
            f"font-size: 17px; font-weight: 800; color: {TEXT_PRIMARY};"
            f"background: transparent; border: none;"
        )
        sb_layout.addWidget(brand)

        accent_line = QFrame()
        accent_line.setFixedSize(40, 2)
        accent_line.setStyleSheet(f"background-color: {ACCENT_FILL}; border: none;")
        sb_layout.addWidget(accent_line)
        sb_layout.addSpacing(8)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet(f"background: {BORDER}; border: none; max-height: 1px; margin: 8px 0;")
        sb_layout.addWidget(sep1)

        self.running_lbl = QLabel("0 running")
        self.running_lbl.setStyleSheet(
            f"font-size: 12px; color: {TEXT_SECONDARY};"
            f"background: transparent; border: none; padding: 4px 0;"
        )
        sb_layout.addWidget(self.running_lbl)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"background: {BORDER}; border: none; max-height: 1px; margin: 8px 0;")
        sb_layout.addWidget(sep2)

        filters_lbl = QLabel("FILTER")
        filters_lbl.setStyleSheet(
            f"font-size: 10px; font-weight: 700; color: {TEXT_DISABLED};"
            f"background: transparent; border: none; letter-spacing: 1.5px; padding: 4px 0 8px 0;"
        )
        sb_layout.addWidget(filters_lbl)

        self._filter_btns: dict[str, QPushButton] = {}
        filter_defs = [
            ("All",     TEXT_PRIMARY),
            ("Running", GREEN),
            ("Stopped", TEXT_SECONDARY),
            ("Failed",  RED),
        ]
        for label, color in filter_defs:
            btn = QPushButton(label)
            btn.setCheckable(False)
            btn.setStyleSheet(sidebar_btn_stylesheet(active=(label == "All")))
            btn.clicked.connect(lambda _, lbl=label: self._set_filter_state(lbl))
            self._filter_btns[label] = btn
            sb_layout.addWidget(btn)

        sb_layout.addStretch()

        # New command button at sidebar bottom
        self.add_btn = QPushButton("+ New Command")
        self.add_btn.setMinimumHeight(40)
        self.add_btn.setStyleSheet(
            f"QPushButton {{ background-color: {ACCENT_FILL}; color: #ffffff;"
            f"border: none; border-radius: 10px; padding: 10px 0;"
            f"font-size: 13px; font-weight: 700; }}"
            f"QPushButton:hover {{ background-color: {ACCENT_HOVER}; }}"
        )
        self.add_btn.clicked.connect(self.open_create_dialog)
        sb_layout.addWidget(self.add_btn)
        root.addWidget(sidebar)

        main_area = QWidget()
        main_area.setStyleSheet(f"background-color: {BG_BASE};")
        main_vbox = QVBoxLayout(main_area)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)

        topbar = QWidget()
        topbar.setFixedHeight(64)
        topbar.setStyleSheet(
            f"background-color: {BG_SIDEBAR}; border-bottom: 1px solid {BORDER};"
        )
        topbar_layout = QHBoxLayout(topbar)
        topbar_layout.setContentsMargins(28, 0, 28, 0)
        topbar_layout.setSpacing(16)

        self.page_title = QLabel("All Commands")
        self.page_title.setStyleSheet(
            f"font-size: 15px; font-weight: 600; color: {TEXT_PRIMARY};"
            f"background: transparent; border: none;"
        )
        topbar_layout.addWidget(self.page_title)
        topbar_layout.addStretch()

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by name or description...")
        self.search_box.setFixedWidth(320)
        self.search_box.setFixedHeight(36)
        self.search_box.textChanged.connect(self.filter_commands)
        topbar_layout.addWidget(self.search_box)

        main_vbox.addWidget(topbar)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(GRID_SPACING)
        self.grid_layout.setContentsMargins(32, 28, 32, 28)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.grid_container)
        main_vbox.addWidget(self.scroll_area, stretch=1)
        root.addWidget(main_area, stretch=1)

        self.status_bar = QStatusBar()
        ver_lbl = QLabel(f"v{APP_VERSION}")
        ver_lbl.setStyleSheet(
            f"font-size: 11px; color: {TEXT_DISABLED};"
            f"background: transparent; border: none; padding-right: 4px;"
        )
        self.status_bar.addPermanentWidget(ver_lbl)
        self.setStatusBar(self.status_bar)

        self.setStyleSheet(APP_STYLESHEET)
        self._update_status_bar()

    def load_commands(self) -> None:
        # Clear existing cards from grid
        while self.grid_layout.count():
            child = self.grid_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self._all_commands = []
        self._cards = {}
        session = SessionLocal()
        try:
            service = CommandService(session)
            commands = service.get_all()
            self._all_commands = commands
            for cmd in commands:
                self.add_command_card(cmd)
        finally:
            session.close()
        self._apply_filter()
        self._update_status_bar()

    def filter_commands(self, text: str) -> None:
        self._filter_text = text.lower()
        self._apply_filter()

    def _set_filter_state(self, state: str) -> None:
        self._filter_state = state
        self.page_title.setText(f"{state} Commands" if state != "All" else "All Commands")
        for lbl, btn in self._filter_btns.items():
            btn.setStyleSheet(sidebar_btn_stylesheet(active=(lbl == state)))
        self._apply_filter()

    def _apply_filter(self) -> None:
        for card in self._cards.values():
            text_ok = (
                not self._filter_text
                or self._filter_text in card.command_obj.name.lower()
                or (card.command_obj.description and self._filter_text in card.command_obj.description.lower())
            )
            state_ok = (
                self._filter_state == "All"
                or card.state == self._filter_state
            )
            card.visible = bool(text_ok and state_ok)
        self._relayout_grid()

    def _relayout_grid(self) -> None:
        # Remove all cards from layout (without destroying them)
        while self.grid_layout.count():
            self.grid_layout.takeAt(0)

        # Fixed card width + grid spacing
        cell_w = CARD_WIDTH + GRID_SPACING
        # Viewport width may be 0 before the window is shown; fall back to the
        # main window width minus the sidebar so the first paint already flows.
        vp = self.scroll_area.viewport().width()
        if vp <= 1:
            vp = max(self.width() - 220, cell_w)
        avail = vp - 56  # minus grid content margins
        cols = max(1, avail // cell_w)

        visible_cards = [c for c in self._cards.values() if c.visible]
        for c in self._cards.values():
            c.setVisible(c.visible)

        for idx, card in enumerate(visible_cards):
            row, col = divmod(idx, cols)
            self.grid_layout.addWidget(
                card, row, col, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
            )

        # Keep cards packed left; trailing column absorbs the extra space
        last = max(cols, 1)
        for i in range(last):
            self.grid_layout.setColumnStretch(i, 0)
        self.grid_layout.setColumnStretch(last, 1)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if hasattr(self, "_cards") and self._cards:
            self._relayout_grid()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if hasattr(self, "_cards") and self._cards:
            self._relayout_grid()

    def add_command_card(self, command: Command) -> None:
        card = CommandCard(command)
        card.run_btn.clicked.connect(lambda _, c=command: self.run_command(c))
        card.stop_btn.clicked.connect(lambda _, c=command: self.stop_command(c))
        card.menu_btn.clicked.connect(lambda _, c=command, crd=card: self._show_card_menu(c, crd))
        card.activated.connect(lambda c=command: self.run_command(c))
        card.update_status(self.process_service.get_state(command.id))
        session = SessionLocal()
        try:
            last_log = ExecutionLogService(session).get_latest(command.id)
            card.set_last_run(last_log.finished_at if last_log else None)
        finally:
            session.close()
        self._cards[command.id] = card

    def _show_card_menu(self, command: Command, card: CommandCard) -> None:
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {BG_CARD}; color: {TEXT_PRIMARY};"
            f"border: 1px solid {BORDER}; border-radius: 8px; padding: 6px; }}"
            f"QMenu::item {{ padding: 8px 20px; border-radius: 6px; }}"
            f"QMenu::item:selected {{ background-color: {BG_ELEVATED}; }}"
            f"QMenu::separator {{ background-color: {BORDER}; margin: 4px 0; }}"
        )
        menu.addAction("  Logs  ", lambda: self.show_logs_for_command(command))
        menu.addAction("  History  ", lambda: self.show_history_for_command(command))
        menu.addSeparator()
        menu.addAction("  Edit  ", lambda: self.edit_command(command))
        menu.addAction("  Duplicate  ", lambda: self.duplicate_command(command))
        menu.addSeparator()
        del_action = menu.addAction("  Delete  ")
        del_action.triggered.connect(lambda: self.delete_command(command))
        menu.exec(card.menu_btn.mapToGlobal(card.menu_btn.rect().bottomLeft()))

    def run_command(self, command: Command) -> None:
        args = command.arguments or []
        env = command.env_vars or {}
        ok = self.process_service.start(
            command.id, command.command, args,
            command.working_directory or "", env
        )
        if not ok:
            QMessageBox.information(self, "Info", f"'{command.name}' is already running.")

    def stop_command(self, command: Command) -> None:
        self.process_service.stop(command.id)

    @Slot(str, str)
    def on_state_changed(self, command_id: str, state: str) -> None:
        cid = int(command_id)
        self.update_card_status(cid, state)
        if state == "Running":
            self._running_ids.add(cid)
        else:
            self._running_ids.discard(cid)
        self._update_status_bar()

    def _update_status_bar(self) -> None:
        count = len(self._running_ids)
        if count > 0:
            self.running_lbl.setStyleSheet(
                f"font-size: 12px; color: {GREEN};"
                f"background: transparent; border: none; padding: 4px 0; font-weight: 600;"
            )
            self.running_lbl.setText(f"{count} running")
        else:
            self.running_lbl.setStyleSheet(
                f"font-size: 12px; color: {TEXT_SECONDARY};"
                f"background: transparent; border: none; padding: 4px 0;"
            )
            self.running_lbl.setText("0 running")
        self.status_bar.showMessage(
            f"  {count} process(es) running  —  {len(self._cards)} command(s) loaded"
        )

    @Slot(str, str, str, int, object)
    def on_log_ready(self, command_id: str, stdout: str, stderr: str,
                     exit_code: int, started_at) -> None:
        cid = int(command_id)
        if cid not in self._cards:
            return  # the command was deleted while running
        session = SessionLocal()
        try:
            service = ExecutionLogService(session)
            service.create({
                "command_id": cid,
                "output": stdout or None,
                "error": stderr or None,
                "exit_code": exit_code,
                "started_at": started_at,
                "finished_at": _now(),
            })
        finally:
            session.close()
        # Refresh last-run timestamp on the card
        card = self._cards.get(cid)
        if card:
            card.set_last_run(_now())

    def update_card_status(self, command_id: int, state: str) -> None:
        card = self._cards.get(command_id)
        if card:
            card.update_status(state)

    def open_create_dialog(self) -> None:
        dialog = CommandDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            session = SessionLocal()
            try:
                service = CommandService(session)
                service.create(dialog.get_data())
                self.load_commands()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create command:\n{e}")
            finally:
                session.close()

    def edit_command(self, command: Command) -> None:
        dialog = CommandDialog(self, command=command)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            session = SessionLocal()
            try:
                service = CommandService(session)
                service.update(command.id, dialog.get_data())
                self.load_commands()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to update command:\n{e}")
            finally:
                session.close()

    def show_logs_for_command(self, command: Command) -> None:
        win = self._log_windows.get(command.id)
        if win is not None:
            try:
                if not win.isVisible():
                    win.show()
                win.raise_()
                win.activateWindow()
                return
            except RuntimeError:
                # Underlying C++ object was deleted; drop the stale reference.
                self._log_windows.pop(command.id, None)

        win = LogWindow(command.id, command.name, self.process_service, self)
        win.finished.connect(lambda *_: self._log_windows.pop(command.id, None))
        self._log_windows[command.id] = win
        win.show()
        win.raise_()
        win.activateWindow()

    def show_history_for_command(self, command: Command) -> None:
        dlg = ExecutionHistoryDialog(command, self)
        dlg.historyCleared.connect(self._on_history_cleared)
        dlg.exec()

    def _on_history_cleared(self, command_id: int) -> None:
        card = self._cards.get(command_id)
        if card:
            card.set_last_run(None)

    def duplicate_command(self, command: Command) -> None:
        data = {
            "name": f"{command.name} (copy)",
            "description": command.description,
            "working_directory": command.working_directory,
            "command": command.command,
            "arguments": list(command.arguments) if command.arguments else [],
            "env_vars": dict(command.env_vars) if command.env_vars else {},
            "auto_run": False,
            "tags": list(command.tags) if command.tags else [],
        }
        session = SessionLocal()
        try:
            service = CommandService(session)
            service.create(data)
            self.load_commands()
        finally:
            session.close()

    def _auto_run_commands(self) -> None:
        for cmd in self._all_commands:
            if cmd.auto_run:
                self.run_command(cmd)

    def delete_command(self, command: Command) -> None:
        reply = QMessageBox.question(
            self, "Confirm", f"Delete '{command.name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.process_service.stop(command.id)
        win = self._log_windows.pop(command.id, None)
        if win is not None:
            try:
                win.close()
            except RuntimeError:
                pass
        session = SessionLocal()
        try:
            if not CommandService(session).delete(command.id):
                QMessageBox.warning(self, "Warning", "Command could not be deleted.")
                return
            ExecutionLogService(session).delete_by_command_id(command.id)
            self.load_commands()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to delete command:\n{e}")
        finally:
            session.close()

    def import_commands(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Import Commands", "", "JSON (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("JSON file must contain an array of commands.")
            for item in data:
                if not isinstance(item, dict) or not item.get("name") or not item.get("command"):
                    raise ValueError("Each command must be an object with 'name' and 'command'.")
            session = SessionLocal()
            try:
                service = CommandService(session)
                for item in data:
                    item = {
                        k: v for k, v in item.items()
                        if k in {"name", "description", "working_directory", "command",
                                 "arguments", "env_vars", "auto_run", "tags"}
                    }
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
        dlg = AboutDialog(self)
        dlg.exec()

    def closeEvent(self, event) -> None:
        self.process_service.stop_all()
        # Pump the event loop until every process exits (the 3s force-kill
        # timer guarantees this terminates).
        deadline = time.monotonic() + 4.0
        while self.process_service.has_running() and time.monotonic() < deadline:
            QCoreApplication.processEvents()
            time.sleep(0.05)
        event.accept()
