"""DevCommandCenter — accessible dark theme (GitHub-inspired, WCAG AA)."""

# ── Surfaces ─────────────────────────────────────────────────────────────────
BG_BASE     = "#0d1117"   # main canvas
BG_SIDEBAR  = "#010409"   # sidebar / topbar (darkest)
BG_CARD     = "#161b22"   # card surface
BG_ELEVATED = "#21262d"   # elevated / hover
BG_INPUT    = "#21262d"   # inputs
BG_CODE     = "#0d1117"   # code block

BORDER       = "#30363d"  # default border
BORDER_HOVER = "#484f58"  # hover border
BORDER_FOCUS = "#4493f8"  # focus ring

# ── Text (all ≥ 4.5:1 on dark surfaces) ──────────────────────────────────────
TEXT_PRIMARY   = "#e6edf3"  # ~14:1  AAA
TEXT_SECONDARY = "#9da7b3"  # ~6.2:1 AA
TEXT_DISABLED  = "#6e7681"  # ~4:1   (large/decorative only)

# ── Accents (bright variants = text on dark; solid variants = fills) ──────────
ACCENT      = "#4493f8"   # primary blue (text/links on dark)
ACCENT_FILL = "#1f6feb"   # blue button fill (white text = 5:1)
ACCENT_HOVER = "#388bfd"

GREEN       = "#3fb950"   # running text on dark (~5.8:1)
GREEN_FILL  = "#238636"   # run button fill (white text = 4.6:1)
GREEN_HOVER = "#2ea043"

RED         = "#ff7b72"   # failed text on dark (~6:1)
RED_FILL    = "#da3633"   # stop/delete fill (white text = 4.5:1)
RED_HOVER   = "#e5534b"

AMBER       = "#d29922"   # warning

STATUS_RUNNING = GREEN
STATUS_STOPPED = TEXT_SECONDARY
STATUS_FAILED  = RED

# ── Legacy aliases ───────────────────────────────────────────────────────────
CYAN                 = ACCENT
ROSE                 = RED
ORANGE               = AMBER
BG_PRIMARY           = BG_BASE
BG_SURFACE           = BG_SIDEBAR
ACCENT_PRIMARY       = ACCENT
ACCENT_PRIMARY_HOVER = ACCENT_HOVER
ACCENT_SUCCESS       = GREEN
ACCENT_SUCCESS_HOVER = GREEN_HOVER
ACCENT_DANGER        = RED
ACCENT_DANGER_HOVER  = RED_HOVER
ACCENT_WARNING       = AMBER

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
    # Solid dark surface + bright colored text => guaranteed ≥4.5:1 contrast.
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


# ── Tag chip ─────────────────────────────────────────────────────────────────
def tag_chip_stylesheet() -> str:
    return (
        f"background-color: {BG_ELEVATED};"
        f"color: #79c0ff;"  # light blue, ~8:1 on dark
        f"border: 1px solid {BORDER};"
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
