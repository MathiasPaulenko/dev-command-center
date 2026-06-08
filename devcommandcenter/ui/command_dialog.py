import json
from typing import Optional

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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from devcommandcenter.database.models import Command


class TagEditor(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._tags: list[str] = []
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Add tag...")
        self.add_btn = QPushButton("+")
        self.add_btn.setFixedWidth(30)
        self.tags_label = QLabel("")
        self.tags_label.setStyleSheet("color: #aaa; font-size: 12px;")
        layout.addWidget(self.input, stretch=1)
        layout.addWidget(self.add_btn)
        layout.addWidget(self.tags_label)
        self.add_btn.clicked.connect(self.add_tag)
        self.input.returnPressed.connect(self.add_tag)

    def add_tag(self) -> None:
        text = self.input.text().strip()
        if text and text not in self._tags:
            self._tags.append(text)
            self._update_label()
        self.input.clear()

    def _update_label(self) -> None:
        self.tags_label.setText(", ".join(self._tags) if self._tags else "")

    def get_tags(self) -> list[str]:
        return list(self._tags)

    def set_tags(self, tags: list[str]) -> None:
        self._tags = list(tags)
        self._update_label()


class CommandDialog(QDialog):
    def __init__(self, parent=None, command: Optional[Command] = None) -> None:
        super().__init__(parent)
        self.command = command
        self.setWindowTitle("Edit Command" if command else "New Command")
        self.resize(500, 400)
        self.setup_ui()
        if command:
            self.load_data(command)

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        form = QFormLayout()
        form.setSpacing(10)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Command name")
        form.addRow("Name *", self.name_input)

        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Short description")
        form.addRow("Description", self.desc_input)

        wd_row = QHBoxLayout()
        self.wd_input = QLineEdit()
        self.wd_input.setPlaceholderText("C:\\projects\\myapp")
        wd_browse = QPushButton("Browse...")
        wd_browse.setFixedWidth(80)
        wd_browse.clicked.connect(self._browse_working_directory)
        wd_row.addWidget(self.wd_input)
        wd_row.addWidget(wd_browse)
        form.addRow("Working Directory", wd_row)

        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("npm, python, docker...")
        form.addRow("Command *", self.command_input)

        self.args_input = QLineEdit()
        self.args_input.setPlaceholderText('e.g. ["run", "dev"]')
        form.addRow("Arguments (JSON array)", self.args_input)

        self.env_input = QTextEdit()
        self.env_input.setPlaceholderText('{"KEY": "value", "NODE_ENV": "development"}')
        self.env_input.setMaximumHeight(80)
        form.addRow("Environment Variables (JSON)", self.env_input)

        self.auto_run_check = QCheckBox("Auto-run on startup")
        form.addRow("", self.auto_run_check)

        self.tags_editor = TagEditor()
        form.addRow("Tags", self.tags_editor)

        layout.addLayout(form)
        layout.addStretch()

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setStyleSheet(
            """
            QDialog {
                background-color: #252526;
                color: #cccccc;
            }
            QLineEdit, QTextEdit {
                background-color: #3c3c3c;
                color: #cccccc;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 6px;
            }
            QPushButton {
                background-color: #0e639c;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #1177bb;
            }
            QLabel {
                color: #cccccc;
            }
            QCheckBox {
                color: #cccccc;
            }
        """
        )

    def load_data(self, command: Command) -> None:
        self.name_input.setText(command.name or "")
        self.desc_input.setText(command.description or "")
        self.wd_input.setText(command.working_directory or "")
        self.command_input.setText(command.command or "")
        self.args_input.setText(json.dumps(command.arguments) if command.arguments else "")
        self.env_input.setText(json.dumps(command.env_vars) if command.env_vars else "")
        self.auto_run_check.setChecked(command.auto_run or False)
        self.tags_editor.set_tags(command.tags or [])

    def get_data(self) -> dict:
        data = {
            "name": self.name_input.text().strip(),
            "description": self.desc_input.text().strip() or None,
            "working_directory": self.wd_input.text().strip() or None,
            "command": self.command_input.text().strip(),
            "arguments": [],
            "env_vars": {},
            "auto_run": self.auto_run_check.isChecked(),
            "tags": self.tags_editor.get_tags(),
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
