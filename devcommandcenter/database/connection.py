from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from devcommandcenter.config import DATABASE_URL
from devcommandcenter.database.models import Base


def _make_engine(url: str) -> Engine:
    """Build the SQLAlchemy engine for the app database.

    In-memory SQLite gives each pooled connection its own empty database, so
    sessions would randomly lose the schema — pin a single shared connection.
    """
    if ":memory:" in url or "mode=memory" in url:
        return create_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url, echo=False)


engine = _make_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
