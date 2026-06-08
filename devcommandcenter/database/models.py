from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from devcommandcenter.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


class Command(Base):
    __tablename__ = "commands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    working_directory: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    command: Mapped[str] = mapped_column(String(512), nullable=False)
    arguments: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    env_vars: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    auto_run: Mapped[bool] = mapped_column(default=False)
    tags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return f"<Command(id={self.id}, name='{self.name}', command='{self.command}')>"


class ExecutionLog(Base):
    __tablename__ = "execution_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    command_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    exit_code: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<ExecutionLog(id={self.id}, command_id={self.command_id})>"
