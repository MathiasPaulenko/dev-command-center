from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from devcommandcenter.config import DATABASE_URL
from devcommandcenter.database.models import Base

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
