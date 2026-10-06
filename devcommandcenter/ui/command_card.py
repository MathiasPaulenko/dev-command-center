"""CommandCard widget — a single command in the main grid."""

from __future__ import annotations

import html
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from devcommandcenter.database.models import Command
from devcommandcenter.ui.theme import (
    BG_CARD,
    BG_CODE,
    BG_ELEVATED,
    BG_INPUT,
    BORDER,
    BORDER_HOVER,
    GREEN,
    GREEN_FILL,
    GREEN_HOVER,
    RED_FILL,
    RED_HOVER,
    STATUS_FAILED,
    STATUS_RUNNING,
    STATUS_STOPPED,
    TEXT_DISABLED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    status_badge_stylesheet,
)

CARD_WIDTH = 320
CARD_HEIGHT = 300


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


class CommandCard(QWidget):
    activated = Signal()

    def __init__(self, command: Command, parent=None) -> None:
        super().__init__(parent)
        self.command_id = command.id
        self.command_obj = command
        self.state = "Stopped"
        self.visible = True
        self.setup_ui()

    def mouseDoubleClickEvent(self, event) -> None:
        self.activated.emit()
        super().mouseDoubleClickEvent(event)

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
        body_layout.setContentsMargins(22, 22, 22, 22)
        body_layout.setSpacing(14)
        outer.addWidget(body, stretch=1)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        self.name_label = QLabel(self.command_obj.name)
        self.name_label.setTextFormat(Qt.TextFormat.PlainText)
        self.name_label.setStyleSheet(
            f"font-size: 16px; font-weight: 700; color: {TEXT_PRIMARY};"
        )
        self.name_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.status_badge = QLabel("Stopped")
        self.status_badge.setStyleSheet(status_badge_stylesheet(STATUS_STOPPED))
        self.menu_btn = QPushButton("⋮")
        self.menu_btn.setFixedSize(26, 26)
        self.menu_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.menu_btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {TEXT_DISABLED};"
            f"border: none; border-radius: 6px; font-size: 16px; padding: 0; }}"
            f"QPushButton:hover {{ color: {TEXT_PRIMARY};"
            f"background-color: {BG_ELEVATED}; }}"
        )
        top_row.addWidget(self.name_label)
        top_row.addStretch()
        top_row.addWidget(self.status_badge)
        top_row.addWidget(self.menu_btn)
        body_layout.addLayout(top_row)

        desc = self.command_obj.description or ""
        if desc:
            self.desc_label = QLabel(desc)
            self.desc_label.setTextFormat(Qt.TextFormat.PlainText)
            self.desc_label.setStyleSheet(
                f"color: {TEXT_SECONDARY}; font-size: 13px;"
            )
            self.desc_label.setWordWrap(True)
            body_layout.addWidget(self.desc_label)

        cmd = html.escape(self.command_obj.command or "")
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

        self.last_run_label = QLabel("")
        self.last_run_label.setStyleSheet(
            f"font-size: 11px; color: {TEXT_DISABLED}; font-style: italic;"
        )
        body_layout.addWidget(self.last_run_label)

        body_layout.addStretch()

        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setStyleSheet(f"background: {BORDER}; border: none; max-height: 1px; margin: 8px 0;")
        body_layout.addWidget(div)

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

        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def update_status(self, state: str) -> None:
        self.state = state
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
