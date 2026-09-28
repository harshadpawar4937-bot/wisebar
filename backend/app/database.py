from __future__ import annotations

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool, StaticPool

from app.config import get_settings


def _on_vercel() -> bool:
    return any(os.environ.get(key) for key in ("VERCEL", "VERCEL_ENV", "VERCEL_URL"))


def _engine_url(url: str) -> str:
    url = (url or "").strip()
    if _on_vercel() and (not url or url.startswith("sqlite")):
        return "sqlite:////tmp/wisebar.db"
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url or "sqlite:///./wisebar.db"


settings = get_settings()
database_url = _engine_url(settings.database_url)
if database_url.startswith("sqlite"):
    engine = create_engine(database_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
else:
    engine = create_engine(database_url, pool_pre_ping=True, poolclass=NullPool)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
