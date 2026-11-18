from __future__ import annotations

from sqlalchemy.orm import Session

from devcommandcenter.database.models import ExecutionLog

_LOG_FIELDS = frozenset({
    "command_id", "output", "error", "exit_code", "started_at", "finished_at",
})


class ExecutionLogService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, data: dict) -> ExecutionLog:
        if data.get("command_id") is None:
            raise ValueError("'command_id' is required")
        log = ExecutionLog(**{k: v for k, v in data.items() if k in _LOG_FIELDS})
        self.session.add(log)
        self.session.commit()
        self.session.refresh(log)
        return log

    def get_by_id(self, log_id: int) -> ExecutionLog | None:
        return (
            self.session.query(ExecutionLog)
            .filter(ExecutionLog.id == log_id)
            .first()
        )

    def get_by_command_id(self, command_id: int,
                          limit: int | None = None) -> list[ExecutionLog]:
        query = (
            self.session.query(ExecutionLog)
            .filter(ExecutionLog.command_id == command_id)
            .order_by(ExecutionLog.started_at.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def get_summaries(self, command_id: int,
                      limit: int | None = None) -> list[tuple]:
        """Metadata-only rows: (id, started_at, finished_at, exit_code).

        Log output can be megabytes per row — listing executions must not
        pull every Text column into memory at once. Fetch the full row with
        ``get_by_id`` only when the user asks for it.
        """
        query = (
            self.session.query(
                ExecutionLog.id,
                ExecutionLog.started_at,
                ExecutionLog.finished_at,
                ExecutionLog.exit_code,
            )
            .filter(ExecutionLog.command_id == command_id)
            .order_by(ExecutionLog.started_at.desc())
        )
        if limit is not None:
            query = query.limit(limit)
        return query.all()

    def get_latest(self, command_id: int) -> ExecutionLog | None:
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
