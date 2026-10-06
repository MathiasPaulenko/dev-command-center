"""DevCommandCenter — accessible dark theme (GitHub-inspired, WCAG AA)."""

BG_BASE     = "#0d1117"
BG_SIDEBAR  = "#010409"
BG_CARD     = "#161b22"
BG_ELEVATED = "#21262d"
BG_INPUT    = "#21262d"
BG_CODE     = "#0d1117"

BORDER       = "#30363d"  # default border
BORDER_HOVER = "#484f58"  # hover border
BORDER_FOCUS = "#4493f8"  # focus ring

TEXT_PRIMARY   = "#e6edf3"
TEXT_SECONDARY = "#9da7b3"
TEXT_DISABLED  = "#6e7681"

ACCENT       = "#4493f8"
ACCENT_FILL  = "#1f6feb"
ACCENT_HOVER = "#388bfd"

GREEN       = "#3fb950"
GREEN_FILL  = "#238636"
GREEN_HOVER = "#2ea043"

RED       = "#ff7b72"
RED_FILL  = "#da3633"
RED_HOVER = "#e5534b"

AMBER = "#d29922"

STATUS_RUNNING = GREEN
STATUS_STOPPED = TEXT_SECONDARY
STATUS_FAILED  = RED

LOG_ERROR = "#f85149"  # stderr text inside log windows

APP_STYLESHEET = f"""
QMainWindow {{
    background-color: {BG_BASE};
    color: {TEXT_PRIMARY};
}}
QWidget {{
    font-size: 13px;
}}
QMenuBar {{
    background-color: {BG_SIDEBAR};
    color: {TEXT_SECONDARY};
    border-bottom: 1px solid {BORDER};
    padding: 2px 6px;
    font-size: 12px;
}}
QMenuBar::item {{ padding: 5px 10px; border-radius: 4px; }}
QMenuBar::item:selected {{ background-color: {BG_ELEVATED}; color: {TEXT_PRIMARY}; }}
QMenu {{
    background-color: {BG_SIDEBAR};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 4px;
}}
QMenu::item {{ padding: 7px 16px; border-radius: 4px; }}
QMenu::item:selected {{ background-color: {BG_ELEVATED}; }}
QMenu::separator {{ background-color: {BORDER}; height: 1px; margin: 3px 8px; }}

QLineEdit {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 9px 14px;
    font-size: 13px;
    selection-background-color: {ACCENT}33;
}}
QLineEdit:focus {{ border-color: {ACCENT}; }}

QTextEdit {{
    background-color: {BG_CODE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 12px;
    font-family: "Cascadia Code", "JetBrains Mono", "Fira Code", "Consolas", monospace;
    font-size: 13px;
    line-height: 1.6;
    selection-background-color: {ACCENT}33;
}}

QPushButton {{
    background-color: {BG_ELEVATED};
    color: {TEXT_SECONDARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 18px;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {BG_INPUT};
    color: {TEXT_PRIMARY};
    border-color: {BORDER_HOVER};
}}
QPushButton:pressed {{ background-color: {BG_SIDEBAR}; }}
QPushButton:disabled {{ color: {TEXT_DISABLED}; border-color: {BORDER}; }}

QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {BORDER};
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {BORDER_HOVER}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

QStatusBar {{
    background-color: {BG_SIDEBAR};
    color: {TEXT_DISABLED};
    border-top: 1px solid {BORDER};
    font-size: 11px;
    padding: 0 20px;
}}
"""

DIALOG_STYLESHEET = f"""
QDialog {{
    background-color: {BG_SIDEBAR};
    color: {TEXT_PRIMARY};
}}
QLabel {{
    color: {TEXT_SECONDARY};
    font-size: 13px;
    background: transparent;
}}
QCheckBox {{
    color: {TEXT_SECONDARY};
    font-size: 13px;
    spacing: 8px;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid {BORDER};
    background-color: {BG_INPUT};
}}
QCheckBox::indicator:checked {{
    background-color: {ACCENT};
    border-color: {ACCENT};
}}
QDialogButtonBox QPushButton {{
    min-width: 88px;
    min-height: 36px;
}}
"""


def status_badge_stylesheet(color: str) -> str:
    return (
        f"background-color: {BG_ELEVATED};"
        f"color: {color};"
        f"border: 1px solid {color};"
        f"border-radius: 20px;"
        f"padding: 4px 14px;"
        f"font-size: 11px;"
        f"font-weight: 700;"
        f"letter-spacing: 0.5px;"
    )


def sidebar_btn_stylesheet(active: bool = False) -> str:
    if active:
        return (
            f"background-color: {BG_ELEVATED};"
            f"color: {TEXT_PRIMARY};"
            f"border: 1px solid {BORDER_HOVER};"
            f"border-radius: 8px;"
            f"padding: 9px 16px;"
            f"font-size: 13px;"
            f"font-weight: 600;"
            f"text-align: left;"
        )
    return (
        f"background-color: transparent;"
        f"color: {TEXT_SECONDARY};"
        f"border: 1px solid transparent;"
        f"border-radius: 8px;"
        f"padding: 9px 16px;"
        f"font-size: 13px;"
        f"text-align: left;"
    )
