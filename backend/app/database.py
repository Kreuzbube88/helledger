from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase

_engine = None
_SessionLocal = None


class Base(DeclarativeBase):
    pass


def _url(path: str) -> str:
    return "sqlite:///:memory:" if path == ":memory:" else f"sqlite:///{path}"


def get_engine():
    global _engine, _SessionLocal
    if _engine is None:
        from app.config import settings
        _engine = create_engine(_url(settings.DATABASE_PATH), connect_args={"check_same_thread": False})
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    return _engine


def get_db() -> Generator[Session, None, None]:
    get_engine()
    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session() -> Session:
    get_engine()
    return _SessionLocal()
