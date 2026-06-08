from typing import List, Optional

from sqlalchemy.orm import Session

from devcommandcenter.database.models import Command


class CommandService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_all(self) -> List[Command]:
        return self.session.query(Command).order_by(Command.created_at.desc()).all()

    def get_by_id(self, command_id: int) -> Optional[Command]:
        return self.session.query(Command).filter(Command.id == command_id).first()

    def create(self, data: dict) -> Command:
        command = Command(**data)
        self.session.add(command)
        self.session.commit()
        self.session.refresh(command)
        return command

    def update(self, command_id: int, data: dict) -> Optional[Command]:
        command = self.get_by_id(command_id)
        if not command:
            return None
        for key, value in data.items():
            setattr(command, key, value)
        self.session.commit()
        self.session.refresh(command)
        return command

    def delete(self, command_id: int) -> bool:
        command = self.get_by_id(command_id)
        if not command:
            return False
        self.session.delete(command)
        self.session.commit()
        return True
