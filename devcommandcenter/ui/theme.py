"""Centralized theme constants and stylesheet helpers for DevCommandCenter."""

# Palette
BG_PRIMARY = "#0d1117"        # deepest background
BG_SURFACE = "#161b22"        # cards, panels
BG_ELEVATED = "#1c2128"      # elevated surfaces
BG_INPUT = "#21262d"         # inputs
BORDER = "#30363d"           # borders
BORDER_HOVER = "#484f58"     # hover borders

TEXT_PRIMARY = "#e6edf3"     # headings, primary text
TEXT_SECONDARY = "#8b949e"  # descriptions, muted text
TEXT_DISABLED = "#484f58"    # disabled text

ACCENT_PRIMARY = "#58a6ff"   # primary action (run, save)
ACCENT_PRIMARY_HOVER = "#79b8ff"
ACCENT_SUCCESS = "#238636"   # running, success
ACCENT_SUCCESS_HOVER = "#2ea043"
ACCENT_DANGER = "#da3633"    # stop, delete, failed
ACCENT_DANGER_HOVER = "#f85149"
ACCENT_WARNING = "#d29922"   # warnings

STATUS_RUNNING = "#3fb950"
STATUS_STOPPED = "#8b949e"
STATUS_FAILED = "#f85149"

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
}}
QMenuBar::item:selected {{
    background-color: {BG_ELEVATED};
}}
QMenu {{
    background-color: {BG_SURFACE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
}}
QMenu::item:selected {{
    background-color: {BG_ELEVATED};
}}

QLineEdit {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 13px;
}}
QLineEdit:focus {{
    border: 1px solid {ACCENT_PRIMARY};
}}

QTextEdit {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 8px;
    font-family: "Consolas", "JetBrains Mono", "Fira Code", monospace;
    font-size: 13px;
}}

QPushButton {{
    background-color: {BG_ELEVATED};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 6px;
    padding: 6px 16px;
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

QSplitter::handle {{
    background-color: {BORDER};
}}

QListWidget {{
    background-color: {BG_PRIMARY};
    border: none;
    outline: none;
}}
QListWidget::item {{
    background: transparent;
    padding: 6px;
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
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid {BORDER};
    background-color: {BG_INPUT};
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT_PRIMARY};
    border-color: {ACCENT_PRIMARY};
}}
QDialogButtonBox QPushButton {{
    min-width: 80px;
}}
"""


def card_stylesheet() -> str:
    return f"""
    QWidget {{
        background-color: {BG_SURFACE};
        border: 1px solid {BORDER};
        border-radius: 10px;
    }}
    QLabel {{
        background: transparent;
        border: none;
    }}
    QPushButton {{
        background-color: {BG_ELEVATED};
        color: {TEXT_PRIMARY};
        border: 1px solid {BORDER};
        border-radius: 6px;
        padding: 5px 12px;
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
    background-color: {color}22;
    color: {color};
    border: 1px solid {color}44;
    border-radius: 10px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: bold;
"""
