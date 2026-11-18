from __future__ import annotations

from sqlalchemy.orm import Session

from devcommandcenter.database.models import Command, ExecutionLog

EDITABLE_FIELDS = frozenset({
    "name",
    "description",
    "working_directory",
    "command",
    "arguments",
    "env_vars",
    "auto_run",
    "tags",
})


def sanitize_command_data(data: dict, *, partial: bool = False) -> dict:
    """Keep only editable fields and validate their shape.

    Args:
        data: Raw input mapping for a command.
        partial: When True (updates), only the provided fields are checked;
            ``name``/``command`` are not required.

    Returns:
        A cleaned dict safe to apply to a ``Command``.

    Raises:
        ValueError: On missing required fields or values of the wrong type.
    """
    if not isinstance(data, dict):
        raise ValueError("command data must be a JSON object")
    clean = {k: v for k, v in data.items() if k in EDITABLE_FIELDS}
    for field in ("name", "command"):
        if field in clean:
            value = clean[field]
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"'{field}' must be a non-empty string")
            clean[field] = value.strip()
        elif not partial:
            raise ValueError(f"'{field}' is required")
    if "arguments" in clean and clean["arguments"] is not None and not isinstance(clean["arguments"], list):
        raise ValueError("'arguments' must be a JSON array")
    if "env_vars" in clean and clean["env_vars"] is not None and not isinstance(clean["env_vars"], dict):
        raise ValueError("'env_vars' must be a JSON object")
    if "tags" in clean and clean["tags"] is not None and not isinstance(clean["tags"], list):
        raise ValueError("'tags' must be a JSON array")
    for field in ("description", "working_directory"):
        if field in clean and clean[field] is not None and not isinstance(clean[field], str):
            clean[field] = str(clean[field])
    if "auto_run" in clean:
        clean["auto_run"] = bool(clean["auto_run"])
    return clean


class CommandService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_all(self) -> list[Command]:
        return self.session.query(Command).order_by(Command.created_at.desc()).all()

    def get_by_id(self, command_id: int) -> Command | None:
        return self.session.query(Command).filter(Command.id == command_id).first()

    def create(self, data: dict) -> Command:
        command = Command(**sanitize_command_data(data))
        self.session.add(command)
        self.session.commit()
        self.session.refresh(command)
        return command

    def create_many(self, items: list[dict]) -> list[Command]:
        """Insert several commands in a single transaction."""
        commands = [Command(**sanitize_command_data(item)) for item in items]
        self.session.add_all(commands)
        self.session.commit()
        for command in commands:
            self.session.refresh(command)
        return commands

    def update(self, command_id: int, data: dict) -> Command | None:
        command = self.get_by_id(command_id)
        if not command:
            return None
        for key, value in sanitize_command_data(data, partial=True).items():
            setattr(command, key, value)
        self.session.commit()
        self.session.refresh(command)
        return command

    def delete(self, command_id: int) -> bool:
        command = self.get_by_id(command_id)
        if not command:
            return False
        # ExecutionLog rows reference the command without a FK constraint;
        # remove them in the same transaction so orphans can't resurface.
        self.session.query(ExecutionLog).filter(
            ExecutionLog.command_id == command_id
        ).delete()
        self.session.delete(command)
        self.session.commit()
        return True
