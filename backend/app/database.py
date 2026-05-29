from collections.abc import Generator
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy import DateTime, String, create_engine
from sqlalchemy.dialects.sqlite import JSON as SQLiteJSON
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.types import JSON

from app.config import get_settings


class Base(DeclarativeBase):
    pass


class ShopRecord(Base):
    __tablename__ = "shops"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    profile: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(SQLiteJSON, "sqlite"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RunRecord(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    shop_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    run: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(SQLiteJSON, "sqlite"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ActivityRecord(Base):
    __tablename__ = "activity_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    event: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(SQLiteJSON, "sqlite"), nullable=False)


class DebugRecord(Base):
    __tablename__ = "debug_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    event: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(SQLiteJSON, "sqlite"), nullable=False)


class BriefRecord(Base):
    __tablename__ = "briefs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    shop_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    brief: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(SQLiteJSON, "sqlite"), nullable=False)


def build_engine(database_url: str):
    if database_url.startswith("sqlite") and "///" in database_url and ":memory:" not in database_url:
        db_path = database_url.split("///", 1)[1]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args, future=True)


engine = build_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_session() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
