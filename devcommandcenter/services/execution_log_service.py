from typing import List, Optional

from sqlalchemy.orm import Session

from devcommandcenter.database.models import ExecutionLog


class ExecutionLogService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: dict) -> ExecutionLog:
        log = ExecutionLog(**data)
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log

    def get_by_command_id(self, command_id: int) -> List[ExecutionLog]:
        return (
            self.session.query(ExecutionLog)
            .filter(ExecutionLog.command_id == command_id)
            .order_by(ExecutionLog.started_at.desc())
            .all()
        )

    def get_latest(self, command_id: int) -> Optional[ExecutionLog]:
        return (
            self.session.query(ExecutionLog)
            .filter(ExecutionLog.command_id == command_id)
            .order_by(ExecutionLog.started_at.desc())
            .first()
        )

    def delete_by_command_id(self, command_id: int) -> int:
        deleted = (
            self.session.query(ExecutionLog)
            .filter(ExecutionLog.command_id == command_id)
            .delete()
        )
        self.session.commit()
        return deleted
