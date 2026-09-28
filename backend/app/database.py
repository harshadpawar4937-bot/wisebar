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
    if _on_vercel():
        return "sqlite:////tmp/wisebar.db"
    url = (url or "").strip()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    return url or "sqlite:///./wisebar.db"


def _build_engine():
    url = _engine_url(get_settings().database_url)
    try:
        if url.startswith("sqlite"):
            return create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
        return create_engine(url, pool_pre_ping=True, poolclass=NullPool)
    except Exception:
        return create_engine("sqlite:////tmp/wisebar.db", connect_args={"check_same_thread": False}, poolclass=StaticPool)


engine = _build_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
