import json
from datetime import datetime

from pathlib import Path

from PySide6.QtCore import QCoreApplication, Qt, Slot
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
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
from devcommandcenter.database.models import Command, ExecutionLog


def _relative_time(dt: datetime | None) -> str:
    if dt is None:
        return "never"
    delta = datetime.now() - dt
    if delta.days > 0:
        return f"{delta.days}d ago"
    mins = delta.seconds // 60
    if mins >= 60:
        return f"{mins // 60}h ago"
    if mins > 0:
        return f"{mins}m ago"
    return "just now"


from devcommandcenter.services.command_service import CommandService
from devcommandcenter.services.execution_log_service import ExecutionLogService
from devcommandcenter.services.process_service import ProcessService
from devcommandcenter.ui.command_dialog import CommandDialog
from devcommandcenter.ui.log_window import LogWindow
from devcommandcenter.ui.theme import (
    ACCENT_FILL,
    ACCENT_HOVER,
    APP_STYLESHEET,
    BG_BASE,
    BG_CARD,
    BG_CODE,
    BG_ELEVATED,
    BG_INPUT,
    BG_PRIMARY,
    BG_SIDEBAR,
    BG_SURFACE,
    BORDER,
    BORDER_HOVER,
    GREEN,
    GREEN_FILL,
    GREEN_HOVER,
    RED,
    RED_FILL,
    RED_HOVER,
    STATUS_FAILED,
    STATUS_RUNNING,
    STATUS_STOPPED,
    TEXT_DISABLED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    card_stylesheet,
    sidebar_btn_stylesheet,
    status_badge_stylesheet,
    tag_chip_stylesheet,
)


class CommandCard(QWidget):
    def __init__(self, command: Command, parent=None) -> None:
        super().__init__(parent)
        self.command_id = command.id
        self.command_obj = command
        self._state = "Stopped"
        self.setup_ui()

    def setup_ui(self) -> None:
        # Outer: accent bar (left strip) + card body
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.accent_bar = QFrame()
        self.accent_bar.setObjectName("accent_bar")
        self.accent_bar.setFixedWidth(4)
        self.accent_bar.setStyleSheet(
            f"background-color: {STATUS_STOPPED}; border: none; border-radius: 3px;"
        )
        outer.addWidget(self.accent_bar)

        body = QWidget()
        body.setObjectName("card_body")
        body.setStyleSheet(
            f"QWidget#card_body {{ background-color: {BG_CARD};"
            f"border: 1px solid {BORDER};"
            f"border-left: none;"
            f"border-top-right-radius: 12px;"
            f"border-bottom-right-radius: 12px; }}"
            f"QLabel {{ background: transparent; border: none; }}"
            f"QPushButton {{ background-color: {BG_ELEVATED}; color: {TEXT_SECONDARY};"
            f"border: 1px solid {BORDER}; border-radius: 7px;"
            f"padding: 7px 14px; font-size: 12px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {BG_INPUT}; color: {TEXT_PRIMARY};"
            f"border-color: {BORDER_HOVER}; }}"
            f"QPushButton:disabled {{ color: {TEXT_DISABLED}; }}"
        )
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(20, 18, 20, 18)
        body_layout.setSpacing(10)
        outer.addWidget(body, stretch=1)

        # ── Name + badge row ──────────────────────────────────
        top_row = QHBoxLayout()
        top_row.setSpacing(10)
        self.name_label = QLabel(self.command_obj.name)
        self.name_label.setStyleSheet(
            f"font-size: 16px; font-weight: 700; color: {TEXT_PRIMARY};"
        )
        self.name_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.status_badge = QLabel("Stopped")
        self.status_badge.setStyleSheet(status_badge_stylesheet(STATUS_STOPPED))
        top_row.addWidget(self.name_label)
        top_row.addStretch()
        top_row.addWidget(self.status_badge)
        body_layout.addLayout(top_row)

        # ── Description ───────────────────────────────────────
        desc = self.command_obj.description or ""
        if desc:
            self.desc_label = QLabel(desc)
            self.desc_label.setStyleSheet(
                f"color: {TEXT_SECONDARY}; font-size: 13px;"
            )
            self.desc_label.setWordWrap(True)
            body_layout.addWidget(self.desc_label)

        # ── Command chip ──────────────────────────────────────
        cmd = self.command_obj.command or ""
        self.cmd_label = QLabel(
            f"<span style='color:{GREEN};'>$</span> "
            f"<span style='color:{TEXT_PRIMARY};'>{cmd}</span>"
        )
        self.cmd_label.setTextFormat(Qt.TextFormat.RichText)
        self.cmd_label.setStyleSheet(
            f"background-color: {BG_CODE};"
            f"border: 1px solid {BORDER}; border-radius: 6px;"
            f"padding: 7px 12px;"
            f"font-family: 'Cascadia Code','JetBrains Mono','Fira Code','Consolas',monospace;"
            f"font-size: 12px;"
        )
        self.cmd_label.setWordWrap(True)
        body_layout.addWidget(self.cmd_label)

        # ── Tags ──────────────────────────────────────────────
        tags = self.command_obj.tags or []
        if tags:
            tags_row = QHBoxLayout()
            tags_row.setSpacing(5)
            tags_row.setContentsMargins(0, 2, 0, 0)
            for tag in tags[:5]:
                pill = QLabel(f"#{tag}")
                pill.setStyleSheet(tag_chip_stylesheet())
                tags_row.addWidget(pill)
            tags_row.addStretch()
            body_layout.addLayout(tags_row)

        # ── Last run info ───────────────────────────────────
        self.last_run_label = QLabel("")
        self.last_run_label.setStyleSheet(
            f"font-size: 11px; color: {TEXT_DISABLED}; font-style: italic;"
        )
        body_layout.addWidget(self.last_run_label)

        body_layout.addStretch()

        # ── Divider ───────────────────────────────────────────
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"background: {BORDER}; border: none; max-height: 1px; margin: 4px 0;")
        body_layout.addWidget(div)

        # ── Run / Stop ────────────────────────────────────────
        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.run_btn = QPushButton("Run")
        self.run_btn.setMinimumHeight(36)
        self.run_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.run_btn.setStyleSheet(
            f"QPushButton {{ background-color: {GREEN_FILL}; color: #ffffff;"
            f"border: none; border-radius: 8px;"
            f"padding: 8px 0; font-size: 13px; font-weight: 600; }}"
            f"QPushButton:hover {{ background-color: {GREEN_HOVER}; }}"
            f"QPushButton:disabled {{ background-color: {BG_ELEVATED}; color: {TEXT_DISABLED}; }}"
        )
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setMinimumHeight(36)
        self.stop_btn.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet(
            f"QPushButton {{ background-color: {RED_FILL}; color: #ffffff;"
            f"border: none; border-radius: 8px;"
            f"padding: 8px 0; font-size: 13px; font-weight: 600; }}"
            f"QPushButton:hover {{ background-color: {RED_HOVER}; }}"
            f"QPushButton:disabled {{ background-color: {BG_ELEVATED}; color: {TEXT_DISABLED}; }}"
        )
        action_row.addWidget(self.run_btn)
        action_row.addWidget(self.stop_btn)
        body_layout.addLayout(action_row)

        # ── Secondary buttons (2 rows of 2) ───────────────────
        sec_style = (
            f"QPushButton {{ background-color: {BG_ELEVATED}; color: {TEXT_SECONDARY};"
            f"border: 1px solid {BORDER}; border-radius: 6px;"
            f"padding: 5px 10px; font-size: 11px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {BG_INPUT}; color: {TEXT_PRIMARY};"
            f"border-color: {BORDER_HOVER}; }}"
        )

        sec_row1 = QHBoxLayout()
        sec_row1.setSpacing(6)
        self.logs_btn = QPushButton("Logs")
        self.logs_btn.setMinimumHeight(30)
        self.history_btn = QPushButton("History")
        self.history_btn.setMinimumHeight(30)
        self.logs_btn.setStyleSheet(sec_style)
        self.history_btn.setStyleSheet(sec_style)
        for b in (self.logs_btn, self.history_btn):
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sec_row1.addWidget(self.logs_btn)
        sec_row1.addWidget(self.history_btn)
        body_layout.addLayout(sec_row1)

        sec_row2 = QHBoxLayout()
        sec_row2.setSpacing(6)
        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setMinimumHeight(30)
        self.duplicate_btn = QPushButton("Duplicate")
        self.duplicate_btn.setMinimumHeight(30)
        self.delete_btn = QPushButton("Delete")
        self.delete_btn.setMinimumHeight(30)
        self.edit_btn.setStyleSheet(sec_style)
        self.duplicate_btn.setStyleSheet(sec_style)
        self.delete_btn.setStyleSheet(
            f"QPushButton {{ background-color: {BG_ELEVATED}; color: {RED};"
            f"border: 1px solid {BORDER}; border-radius: 6px;"
            f"padding: 5px 10px; font-size: 11px; font-weight: 500; }}"
            f"QPushButton:hover {{ background-color: {RED_FILL}; color: #ffffff; border-color: {RED_FILL}; }}"
        )
        for b in (self.edit_btn, self.duplicate_btn, self.delete_btn):
            b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sec_row2.addWidget(self.edit_btn)
        sec_row2.addWidget(self.duplicate_btn)
        sec_row2.addWidget(self.delete_btn)
        body_layout.addLayout(sec_row2)

        self.setFixedSize(320, 300)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def update_status(self, state: str) -> None:
        self._state = state
        color_map = {
            "Running": STATUS_RUNNING,
            "Stopped": STATUS_STOPPED,
            "Failed":  STATUS_FAILED,
        }
        color = color_map.get(state, STATUS_STOPPED)
        self.status_badge.setText(state)
        self.status_badge.setStyleSheet(status_badge_stylesheet(color))
        self.accent_bar.setStyleSheet(
            f"background-color: {color}; border: none; border-radius: 3px;"
        )
        self.run_btn.setEnabled(state != "Running")
        self.stop_btn.setEnabled(state == "Running")

    def set_last_run(self, dt: datetime | None) -> None:
        text = _relative_time(dt) if dt else "never run"
        self.last_run_label.setText(f"Last run: {text}")


class ExecutionHistoryDialog(QDialog):
    def __init__(self, command: Command, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Execution History: {command.name}")
        self.resize(700, 500)
        self.setup_ui()
        self._load_history(command.id)

    def setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # Header
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

        # Body
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

        # Footer
        footer = QWidget()
        footer.setFixedHeight(64)
        footer.setStyleSheet(
            f"background-color: {BG_CARD}; border-top: 1px solid {BORDER};"
        )
        footer_layout = QHBoxLayout(footer)
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_layout.setContentsMargins(20, 0, 20, 0)
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(36)
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        root.addWidget(footer)

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
            finished = log.finished_at.strftime("%Y-%m-%d %H:%M:%S") if log.finished_at else "?"
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


class AboutDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"About {APP_NAME}")
        self.resize(480, 580)
        self.setMinimumSize(440, 520)
        self.setup_ui()

    def setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # Header with logo and title
        header = QWidget()
        header.setStyleSheet(
            f"background-color: {BG_CARD}; border-bottom: 1px solid {BORDER};"
        )
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setSpacing(12)
        header_layout.setContentsMargins(28, 32, 28, 28)

        # Logo
        logo_lbl = QLabel()
        logo_lbl.setPixmap(self._load_logo(80))
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(logo_lbl)

        # App name
        name_lbl = QLabel(APP_NAME)
        name_lbl.setStyleSheet(
            f"font-size: 24px; font-weight: 700; color: {TEXT_PRIMARY};"
            f"background: transparent; border: none;"
        )
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(name_lbl)

        # Version badge
        version_lbl = QLabel(f"v{APP_VERSION}")
        version_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {ACCENT_FILL};"
            f"background-color: {BG_ELEVATED}; border: 1px solid {ACCENT_FILL};"
            f"border-radius: 12px; padding: 4px 14px;"
        )
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(version_lbl)

        root.addWidget(header)

        # Body
        body = QWidget()
        body.setStyleSheet(f"background-color: {BG_BASE};")
        body_layout = QVBoxLayout(body)
        body_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_layout.setSpacing(16)
        body_layout.setContentsMargins(32, 28, 32, 28)

        desc = QLabel(
            "A modern desktop app for managing and running\n"
            "your development commands with style."
        )
        desc.setStyleSheet(
            f"font-size: 14px; color: {TEXT_SECONDARY}; line-height: 1.5;"
            f"background: transparent; border: none;"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        body_layout.addWidget(desc)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {BORDER};")
        body_layout.addWidget(sep)

        # Features list
        features = QLabel(
            "<ul style='margin-left: 20px;'>"
            "<li>Save and organize commands as cards</li>"
            "<li>Run, stop and monitor processes in real time</li>"
            "<li>Persistent logs for every execution</li>"
            "<li>Filter by status: All, Running, Stopped, Failed</li>"
            "</ul>"
        )
        features.setStyleSheet(
            f"font-size: 13px; color: {TEXT_SECONDARY}; line-height: 1.6;"
            f"background: transparent; border: none;"
        )
        features.setTextFormat(Qt.TextFormat.RichText)
        body_layout.addWidget(features)

        body_layout.addStretch()

        # Credits
        credits = QLabel("Built with Python 3.12 + PySide6 + SQLite")
        credits.setStyleSheet(
            f"font-size: 12px; color: {TEXT_DISABLED};"
            f"background: transparent; border: none;"
        )
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_layout.addWidget(credits)

        # Developer & License
        dev = QLabel("Developed by <b>Mathias Paulenko Echeverz</b>")
        dev.setStyleSheet(
            f"font-size: 12px; color: {TEXT_SECONDARY};"
            f"background: transparent; border: none;"
        )
        dev.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_layout.addWidget(dev)

        license_lbl = QLabel("Licensed under MIT")
        license_lbl.setStyleSheet(
            f"font-size: 12px; color: {TEXT_DISABLED};"
            f"background: transparent; border: none;"
        )
        license_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_layout.addWidget(license_lbl)

        # GitHub link
        link_lbl = QLabel(
            '<a href="https://github.com/MathiasPaulenko/dev-command-center" '
            'style="color:#4493f8;text-decoration:none;">'
            'github.com/MathiasPaulenko/dev-command-center</a>'
        )
        link_lbl.setStyleSheet(
            f"font-size: 12px; background: transparent; border: none;"
        )
        link_lbl.setTextFormat(Qt.TextFormat.RichText)
        link_lbl.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextBrowserInteraction
        )
        link_lbl.setOpenExternalLinks(True)
        link_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_layout.addWidget(link_lbl)

        root.addWidget(body, stretch=1)

        # Footer
        footer = QWidget()
        footer.setFixedHeight(72)
        footer.setStyleSheet(
            f"background-color: {BG_CARD}; border-top: 1px solid {BORDER};"
        )
        footer_layout = QHBoxLayout(footer)
        footer_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_layout.setContentsMargins(28, 0, 28, 0)
        close_btn = QPushButton("Close")
        close_btn.setMinimumHeight(38)
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        root.addWidget(footer)

    def _load_logo(self, size: int) -> QPixmap:
        svg_path = Path(__file__).parent.parent.parent / "assets" / "logo.svg"
        if not svg_path.exists():
            return QPixmap(size, size)
        renderer = QSvgRenderer(str(svg_path))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("DevCommandCenter")
        self.resize(1440, 900)
        self.process_service = ProcessService()
        self.process_service.stateChanged.connect(self.on_state_changed)
        self.process_service.logReady.connect(self.on_log_ready)
        self._command_names: dict[int, str] = {}
        self._running_ids: set[int] = set()
        self._log_windows: dict[int, LogWindow] = {}
        self._cards: dict[int, CommandCard] = {}
        self._filter_state: str = "All"
        self._filter_text: str = ""
        self.setup_ui()
        self.load_commands()
        self._auto_run_commands()

    def setup_ui(self) -> None:
        # ── Menu bar (minimal) ────────────────────────────────
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

        # ══ SIDEBAR ═══════════════════════════════════════════
        sidebar = QWidget()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(
            f"background-color: {BG_SIDEBAR};"
            f"border-right: 1px solid {BORDER};"
        )
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(16, 24, 16, 20)
        sb_layout.setSpacing(4)

        # Brand
        brand = QLabel("DevCmd\nCenter")
        brand.setStyleSheet(
            f"font-size: 20px; font-weight: 800; color: {TEXT_PRIMARY};"
            f"background: transparent; border: none; letter-spacing: -0.5px;"
        )
        sb_layout.addWidget(brand)

        ver_lbl = QLabel(f"v{APP_VERSION}")
        ver_lbl.setStyleSheet(
            f"font-size: 11px; color: {TEXT_DISABLED};"
            f"background: transparent; border: none; margin-bottom: 16px;"
        )
        sb_layout.addWidget(ver_lbl)

        # Running counter
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

        # Filter buttons
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

        # ══ MAIN AREA ═════════════════════════════════════════
        main_area = QWidget()
        main_area.setStyleSheet(f"background-color: {BG_BASE};")
        main_vbox = QVBoxLayout(main_area)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)

        # ── Top bar (search + title) ──────────────────────────
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
        self.search_box.setPlaceholderText("Search by name, description or tag...")
        self.search_box.setFixedWidth(320)
        self.search_box.setFixedHeight(36)
        self.search_box.textChanged.connect(self.filter_commands)
        topbar_layout.addWidget(self.search_box)
        main_vbox.addWidget(topbar)

        # ── Grid scroll area ──────────────────────────────────
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: transparent; border: none;")

        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background-color: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(28, 24, 28, 24)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.grid_container)
        main_vbox.addWidget(self.scroll_area, stretch=1)
        root.addWidget(main_area, stretch=1)

        # ── Status bar ────────────────────────────────────────
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.setStyleSheet(APP_STYLESHEET)
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
            for cmd in commands:
                self._command_names[cmd.id] = cmd.name
                self.add_command_card(cmd)
        finally:
            session.close()
        self._relayout_grid()

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
                or any(self._filter_text in t.lower() for t in (card.command_obj.tags or []))
            )
            state_ok = (
                self._filter_state == "All"
                or card._state == self._filter_state
            )
            card._visible = text_ok and state_ok
        self._relayout_grid()

    def _relayout_grid(self) -> None:
        # Remove all cards from layout (without destroying them)
        while self.grid_layout.count():
            self.grid_layout.takeAt(0)

        # Fixed card width (320) + grid spacing (16)
        CARD_W = 320 + 16
        # Viewport width may be 0 before the window is shown; fall back to the
        # main window width minus the sidebar so the first paint already flows.
        vp = self.scroll_area.viewport().width()
        if vp <= 1:
            vp = max(self.width() - 220, CARD_W)
        avail = vp - 56  # minus grid content margins
        cols = max(1, avail // CARD_W)

        visible_cards = [
            c for c in self._cards.values() if getattr(c, "_visible", True)
        ]
        for c in self._cards.values():
            c.setVisible(getattr(c, "_visible", True))

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
        card._visible = True
        card.run_btn.clicked.connect(lambda _, c=command: self.run_command(c))
        card.stop_btn.clicked.connect(lambda _, c=command: self.stop_command(c))
        card.logs_btn.clicked.connect(lambda _, c=command: self.show_logs_for_command(c))
        card.history_btn.clicked.connect(lambda _, c=command: self.show_history_for_command(c))
        card.edit_btn.clicked.connect(lambda _, c=command: self.edit_command(c))
        card.duplicate_btn.clicked.connect(lambda _, c=command: self.duplicate_command(c))
        card.delete_btn.clicked.connect(lambda _, c=command: self.delete_command(c))
        card.mouseDoubleClickEvent = lambda ev, c=command: self.run_command(c)
        current_state = self.process_service.get_state(command.id)
        card.update_status(current_state)
        # Load last run timestamp
        session = SessionLocal()
        try:
            last_log = ExecutionLogService(session).get_latest(command.id)
            card.set_last_run(last_log.finished_at if last_log else None)
        finally:
            session.close()
        self._cards[command.id] = card

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

    def _on_item_double_clicked(self, item) -> None:
        pass

    @Slot(str, str, str, int)
    def on_log_ready(self, command_id: str, stdout: str, stderr: str, exit_code: int) -> None:
        cid = int(command_id)
        session = SessionLocal()
        try:
            service = ExecutionLogService(session)
            service.create({
                "command_id": cid,
                "output": stdout or None,
                "error": stderr or None,
                "exit_code": exit_code,
                "finished_at": datetime.utcnow(),
            })
        finally:
            session.close()
        # Refresh last-run timestamp on the card
        card = self._cards.get(cid)
        if card:
            card.set_last_run(datetime.utcnow())

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
        dlg.exec()

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
        dlg = AboutDialog(self)
        dlg.exec()

    def closeEvent(self, event) -> None:
        self.process_service.stop_all()
        for _ in range(20):
            QCoreApplication.processEvents()
        event.accept()
