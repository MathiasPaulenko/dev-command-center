import json
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devcommandcenter.database.models import Command
from devcommandcenter.ui.theme import (
    BG_BASE,
    BG_CARD,
    BG_ELEVATED,
    BG_INPUT,
    BORDER,
    BORDER_FOCUS,
    BORDER_HOVER,
    GREEN,
    TEXT_DISABLED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
)


class CommandDialog(QDialog):
    def __init__(self, parent=None, command: Optional[Command] = None) -> None:
        super().__init__(parent)
        self.command = command
        self.setWindowTitle("Edit Command" if command else "New Command")
        self.resize(600, 640)
        self.setMinimumSize(520, 560)
        self.setup_ui()
        if command:
            self.load_data(command)

    def setup_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Header ────────────────────────────────────────────
        header = QWidget()
        header.setFixedHeight(64)
        header.setStyleSheet(
            f"background-color: {BG_CARD}; border-bottom: 1px solid {BORDER};"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(28, 0, 28, 0)
        title = QLabel(self.windowTitle())
        title.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {TEXT_PRIMARY};"
            f"background: transparent; border: none;"
        )
        header_layout.addWidget(title)
        header_layout.addStretch()
        root.addWidget(header)

        # ── Scrollable content ────────────────────────────────
        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background-color: {BG_BASE};")
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(18)
        layout.setContentsMargins(28, 24, 28, 24)

        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)

        label_style = f"color: {TEXT_SECONDARY}; font-size: 13px; font-weight: 500;"

        lbl_name = QLabel("Name *")
        lbl_name.setStyleSheet(label_style)
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. Start dev server")
        self.name_input.setMinimumHeight(38)
        form.addRow(lbl_name, self.name_input)

        lbl_desc = QLabel("Description")
        lbl_desc.setStyleSheet(label_style)
        self.desc_input = QTextEdit()
        self.desc_input.setPlaceholderText("What does this command do?")
        self.desc_input.setMaximumHeight(80)
        self.desc_input.setMinimumHeight(60)
        form.addRow(lbl_desc, self.desc_input)

        lbl_wd = QLabel("Working Directory")
        lbl_wd.setStyleSheet(label_style)
        wd_row = QHBoxLayout()
        wd_row.setSpacing(8)
        self.wd_input = QLineEdit()
        self.wd_input.setPlaceholderText("C:\\projects\\myapp")
        self.wd_input.setMinimumHeight(36)
        wd_browse = QPushButton("Browse...")
        wd_browse.setFixedWidth(90)
        wd_browse.setMinimumHeight(36)
        wd_browse.clicked.connect(self._browse_working_directory)
        wd_row.addWidget(self.wd_input, stretch=1)
        wd_row.addWidget(wd_browse)
        form.addRow(lbl_wd, wd_row)

        lbl_cmd = QLabel("Command *")
        lbl_cmd.setStyleSheet(label_style)
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Executable name, e.g. npm")
        self.command_input.setMinimumHeight(38)
        self.command_input.setStyleSheet(
            f"QLineEdit {{ background-color: {BG_INPUT}; color: {TEXT_PRIMARY};"
            f"border: 1px solid {BORDER}; border-radius: 8px; padding: 8px 14px;"
            f"font-family: 'Cascadia Code','JetBrains Mono','Fira Code','Consolas',monospace; }}"
            f"QLineEdit:focus {{ border-color: {BORDER_FOCUS}; }}"
        )
        form.addRow(lbl_cmd, self.command_input)

        lbl_args = QLabel("Arguments (JSON)")
        lbl_args.setStyleSheet(label_style)
        self.args_input = QLineEdit()
        self.args_input.setPlaceholderText('["run", "dev"]')
        self.args_input.setMinimumHeight(36)
        self.args_input.setStyleSheet(
            f"QLineEdit {{ background-color: {BG_INPUT}; color: {TEXT_PRIMARY};"
            f"border: 1px solid {BORDER}; border-radius: 8px; padding: 8px 14px;"
            f"font-family: 'Cascadia Code','JetBrains Mono','Fira Code','Consolas',monospace; }}"
            f"QLineEdit:focus {{ border-color: {BORDER_FOCUS}; }}"
        )
        form.addRow(lbl_args, self.args_input)

        lbl_env = QLabel("Environment Variables (JSON)")
        lbl_env.setStyleSheet(label_style)
        self.env_input = QTextEdit()
        self.env_input.setPlaceholderText('{\n  "KEY": "value",\n  "NODE_ENV": "development"\n}')
        self.env_input.setMaximumHeight(120)
        self.env_input.setMinimumHeight(80)
        self.env_input.setStyleSheet(
            f"QTextEdit {{ background-color: {BG_INPUT}; color: {TEXT_PRIMARY};"
            f"border: 1px solid {BORDER}; border-radius: 8px; padding: 10px 14px;"
            f"font-family: 'Cascadia Code','JetBrains Mono','Fira Code','Consolas',monospace;"
            f"font-size: 12px; }}"
            f"QTextEdit:focus {{ border-color: {BORDER_FOCUS}; }}"
        )
        form.addRow(lbl_env, self.env_input)

        self.auto_run_check = QCheckBox("Auto-run on startup")
        self.auto_run_check.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 13px; spacing: 6px;")
        form.addRow("", self.auto_run_check)

        layout.addLayout(form)
        layout.addStretch()
        root.addWidget(scroll_content, stretch=1)

        footer = QWidget()
        footer.setFixedHeight(72)
        footer.setStyleSheet(
            f"background-color: {BG_CARD}; border-top: 1px solid {BORDER};"
        )
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(28, 0, 28, 0)
        footer_layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        for btn in (
            buttons.button(QDialogButtonBox.StandardButton.Save),
            buttons.button(QDialogButtonBox.StandardButton.Cancel),
        ):
            if btn:
                btn.setMinimumHeight(38)
                btn.setMinimumWidth(90)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        footer_layout.addWidget(buttons)
        root.addWidget(footer)

    def load_data(self, command: Command) -> None:
        self.name_input.setText(command.name or "")
        self.desc_input.setText(command.description or "")
        self.wd_input.setText(command.working_directory or "")
        self.command_input.setText(command.command or "")
        self.args_input.setText(json.dumps(command.arguments) if command.arguments else "")
        self.env_input.setText(json.dumps(command.env_vars) if command.env_vars else "")
        self.auto_run_check.setChecked(command.auto_run or False)

    def get_data(self) -> dict:
        data = {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.text().strip() or None,
            "working_directory": self.wd_input.text().strip() or None,
            "command": self.command_input.text().strip(),
            "arguments": [],
            "env_vars": {},
            "auto_run": self.auto_run_check.isChecked(),
        }
        args_text = self.args_input.text().strip()
        if args_text:
            try:
                data["arguments"] = json.loads(args_text)
            except json.JSONDecodeError:
                pass
        env_text = self.env_input.toPlainText().strip()
        if env_text:
            try:
                data["env_vars"] = json.loads(env_text)
            except json.JSONDecodeError:
                pass
        return data

    def accept(self) -> None:
        if not self.name_input.text().strip() or not self.command_input.text().strip():
            QMessageBox.warning(self, "Validation", "Name and Command are required.")
            return
        args_text = self.args_input.text().strip()
        if args_text:
            try:
                json.loads(args_text)
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Validation", "Arguments must be a valid JSON array.")
                return
        env_text = self.env_input.toPlainText().strip()
        if env_text:
            try:
                json.loads(env_text)
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Validation", "Environment variables must be valid JSON.")
                return
        super().accept()

    def _browse_working_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Working Directory")
        if path:
            self.wd_input.setText(path)
