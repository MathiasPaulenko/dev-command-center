"""DevCommandCenter — Obsidian theme."""

# ── Palette ──────────────────────────────────────────────────────────────────
BG_BASE     = "#0b0b0f"   # near-black base
BG_SIDEBAR  = "#0e0e13"   # sidebar surface
BG_CARD     = "#131318"   # card background
BG_ELEVATED = "#1a1a22"   # elevated / hover
BG_INPUT    = "#20202c"   # inputs / chips
BG_CODE     = "#181820"   # code block

BORDER       = "#252535"  # default border
BORDER_HOVER = "#383850"  # hover border
BORDER_FOCUS = "#22d3ee"  # focus ring

TEXT_PRIMARY   = "#e2e2ef"  # primary text
TEXT_SECONDARY = "#7070a0"  # secondary / muted
TEXT_DISABLED  = "#404058"  # disabled

CYAN    = "#22d3ee"   # primary accent
GREEN   = "#10b981"   # running / success
ROSE    = "#f43f5e"   # danger / failed
ORANGE  = "#f97316"   # warning

STATUS_RUNNING = GREEN
STATUS_STOPPED = TEXT_SECONDARY
STATUS_FAILED  = ROSE

# Legacy aliases kept for compatibility
BG_PRIMARY          = BG_BASE
BG_SURFACE          = BG_SIDEBAR
ACCENT_PRIMARY      = CYAN
ACCENT_PRIMARY_HOVER = "#38bdf8"
ACCENT_SUCCESS      = GREEN
ACCENT_SUCCESS_HOVER = "#34d399"
ACCENT_DANGER       = ROSE
ACCENT_DANGER_HOVER = "#fb7185"
ACCENT_WARNING      = ORANGE

# ── App-wide Qt stylesheet ────────────────────────────────────────────────────
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
    selection-background-color: {CYAN}33;
}}
QLineEdit:focus {{ border-color: {CYAN}; }}

QTextEdit {{
    background-color: {BG_CODE};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 12px;
    font-family: "Cascadia Code", "JetBrains Mono", "Fira Code", "Consolas", monospace;
    font-size: 13px;
    line-height: 1.6;
    selection-background-color: {CYAN}33;
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

# ── Dialog stylesheet ────────────────────────────────────────────────────────
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
    background-color: {CYAN};
    border-color: {CYAN};
}}
QDialogButtonBox QPushButton {{
    min-width: 88px;
    min-height: 36px;
}}
"""


# ── Card stylesheet ───────────────────────────────────────────────────────────
def card_stylesheet() -> str:
    return f"""
    QWidget {{
        background-color: {BG_CARD};
        border: 1px solid {BORDER};
        border-radius: 12px;
    }}
    QLabel {{
        background: transparent;
        border: none;
        color: {TEXT_SECONDARY};
    }}
    QPushButton {{
        background-color: {BG_ELEVATED};
        color: {TEXT_SECONDARY};
        border: 1px solid {BORDER};
        border-radius: 7px;
        padding: 7px 14px;
        font-size: 12px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {BG_INPUT};
        color: {TEXT_PRIMARY};
        border-color: {BORDER_HOVER};
    }}
    QPushButton:pressed {{ background-color: {BG_SIDEBAR}; }}
    QPushButton:disabled {{ color: {TEXT_DISABLED}; border-color: {BORDER}; }}
"""


# ── Status badge ─────────────────────────────────────────────────────────────
def status_badge_stylesheet(color: str) -> str:
    return (
        f"background-color: {color}1a;"
        f"color: {color};"
        f"border: 1px solid {color}40;"
        f"border-radius: 20px;"
        f"padding: 3px 14px;"
        f"font-size: 11px;"
        f"font-weight: 600;"
        f"letter-spacing: 0.8px;"
    )


# ── Tag chip ─────────────────────────────────────────────────────────────────
def tag_chip_stylesheet() -> str:
    return (
        f"background-color: {CYAN}12;"
        f"color: {CYAN}cc;"
        f"border: 1px solid {CYAN}25;"
        f"border-radius: 6px;"
        f"padding: 2px 9px;"
        f"font-size: 11px;"
    )


# ── Sidebar filter button ────────────────────────────────────────────────────
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
