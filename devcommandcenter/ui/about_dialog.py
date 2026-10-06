"""About dialog — logo, version, credits."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from devcommandcenter.config import APP_NAME, APP_VERSION, resource_path
from devcommandcenter.ui.theme import (
    ACCENT_FILL,
    BG_BASE,
    BG_CARD,
    BG_ELEVATED,
    BORDER,
    TEXT_DISABLED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


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

        header = QWidget()
        header.setStyleSheet(
            f"background-color: {BG_CARD}; border-bottom: 1px solid {BORDER};"
        )
        header_layout = QVBoxLayout(header)
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setSpacing(12)
        header_layout.setContentsMargins(28, 32, 28, 28)

        logo_lbl = QLabel()
        logo_lbl.setPixmap(self._load_logo(80))
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(logo_lbl)

        name_lbl = QLabel(APP_NAME)
        name_lbl.setStyleSheet(
            f"font-size: 24px; font-weight: 700; color: {TEXT_PRIMARY};"
            f"background: transparent; border: none;"
        )
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(name_lbl)

        version_lbl = QLabel(f"v{APP_VERSION}")
        version_lbl.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: {ACCENT_FILL};"
            f"background-color: {BG_ELEVATED}; border: 1px solid {ACCENT_FILL};"
            f"border-radius: 12px; padding: 4px 14px;"
        )
        version_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(version_lbl)

        root.addWidget(header)

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

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background-color: {BORDER};")
        body_layout.addWidget(sep)

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

        credits = QLabel("Built with Python 3.12 + PySide6 + SQLite")
        credits.setStyleSheet(
            f"font-size: 12px; color: {TEXT_DISABLED};"
            f"background: transparent; border: none;"
        )
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body_layout.addWidget(credits)

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
        svg_path = resource_path("assets/logo.svg")
        if not svg_path.exists():
            return QPixmap(size, size)
        renderer = QSvgRenderer(str(svg_path))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        # render() without bounds draws at the SVG's default size and clips
        # smaller pixmaps — always scale to the target rect
        renderer.render(painter, QRectF(0, 0, size, size))
        painter.end()
        return pixmap
