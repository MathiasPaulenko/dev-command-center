"""Centralized theme constants and stylesheet helpers for DevCommandCenter."""

# Palette — Modern Dark (slightly warmer, higher contrast)
BG_PRIMARY = "#0f1419"
BG_SURFACE = "#1a1f2e"
BG_ELEVATED = "#212736"
BG_INPUT = "#2a3142"
BORDER = "#3d4554"
BORDER_HOVER = "#556070"
BORDER_FOCUS = "#7aa2f7"

TEXT_PRIMARY = "#c0caf5"
TEXT_SECONDARY = "#a9b1d6"
TEXT_DISABLED = "#565f89"

ACCENT_PRIMARY = "#7aa2f7"
ACCENT_PRIMARY_HOVER = "#bb9af7"
ACCENT_SUCCESS = "#73daca"
ACCENT_SUCCESS_HOVER = "#9ece6a"
ACCENT_DANGER = "#f7768e"
ACCENT_DANGER_HOVER = "#ff9e64"
ACCENT_WARNING = "#e0af68"

STATUS_RUNNING = "#73daca"
STATUS_STOPPED = "#565f89"
STATUS_FAILED = "#f7768e"

# Global application stylesheet
APP_STYLESHEET = f"""
QMainWindow {{
    background-color: {BG_PRIMARY};
    color: {TEXT_PRIMARY};
}}

QMenuBar {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border-bottom: 1px solid {BORDER};
    padding: 4px;
}}
QMenuBar::item {{
    padding: 4px 12px;
    border-radius: 4px;
}}
QMenuBar::item:selected {{
    background-color: {BG_ELEVATED};
}}
QMenu {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px;
}}
QMenu::item {{
    padding: 6px 16px;
    border-radius: 4px;
}}
QMenu::item:selected {{
    background-color: {BG_ELEVATED};
}}

QLineEdit {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px 14px;
    font-size: 13px;
}}
QLineEdit:focus {{
    border: 1px solid {BORDER_FOCUS};
}}
QLineEdit::placeholder {{
    color: {TEXT_DISABLED};
}}

QTextEdit {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 10px;
    font-family: "JetBrains Mono", "Fira Code", "Consolas", monospace;
    font-size: 13px;
}}

QPushButton {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {BG_INPUT};
    border-color: {BORDER_HOVER};
}}
QPushButton:pressed {{
    background-color: {BG_SURFACE};
}}
QPushButton:disabled {{
    color: {TEXT_DISABLED};
    border-color: {BORDER};
}}

QStatusBar {{
    background-color: {BG_SURFACE};
    color: {TEXT_SECONDARY};
    border-top: 1px solid {BORDER};
}}

QScrollBar:vertical {{
    background-color: {BG_PRIMARY};
    width: 10px;
    border-radius: 5px;
}}
QScrollBar::handle:vertical {{
    background-color: {BORDER};
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {BORDER_HOVER};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QListWidget {{
    background-color: {BG_PRIMARY};
    border: none;
    outline: none;
}}
QListWidget::item {{
    background: transparent;
    padding: 8px;
}}
QListWidget::item:selected {{
    background: transparent;
}}
"""

DIALOG_STYLESHEET = f"""
QDialog {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
}}
QLabel {{
    color: {TEXT_PRIMARY};
    font-size: 13px;
}}
QCheckBox {{
    color: {TEXT_SECONDARY};
    font-size: 13px;
}}
QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border-radius: 6px;
    border: 1px solid {BORDER};
    background-color: {BG_INPUT};
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT_PRIMARY};
    border-color: {ACCENT_PRIMARY};
}}
QDialogButtonBox QPushButton {{
    min-width: 90px;
}}
"""


def card_stylesheet() -> str:
    return f"""
    QWidget {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER};
        border-radius: 14px;
    }}
    QWidget:hover {{
        border: 1px solid {BORDER_HOVER};
    }}
    QLabel {{
        background: transparent;
        border: none;
    }}
    QPushButton {{
        background-color: {BG_ELEVATED};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 8px;
        padding: 6px 14px;
        font-size: 12px;
        font-weight: 500;
        min-width: 50px;
    }}
    QPushButton:hover {{
        background-color: {BG_INPUT};
        border-color: {BORDER_HOVER};
    }}
    QPushButton:pressed {{
        background-color: {BG_SURFACE};
    }}
    QPushButton:disabled {{
        color: {TEXT_DISABLED};
    }}
"""


def status_badge_stylesheet(color: str) -> str:
    return f"""
    background-color: {color}18;
    color: {color};
    border: 1px solid {color}40;
    border-radius: 12px;
    padding: 3px 12px;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 0.5px;
"""
