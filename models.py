"""SQLAlchemy models and database helpers for participant state."""

from __future__ import annotations

import json
import os
from datetime import date, datetime
from typing import Iterable

from sqlalchemy import Boolean, Date, DateTime, Integer, String, Text, create_engine, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./pushups.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


class Base(DeclarativeBase):
    pass


class Participant(Base):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    person_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    room_id: Mapped[str] = mapped_column(String(128))
    level: Mapped[int] = mapped_column(Integer)
    starting_week: Mapped[int] = mapped_column(Integer, default=1)
    start_date: Mapped[date] = mapped_column(Date)
    schedule_days: Mapped[str] = mapped_column(Text, default="[]")
    reminder_time: Mapped[str] = mapped_column(String(5), default="08:00")
    current_week: Mapped[int] = mapped_column(Integer, default=1)
    current_day: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    @property
    def schedule_day_numbers(self) -> list[int]:
        return json.loads(self.schedule_days or "[]")

    def set_schedule_days(self, days: Iterable[int]) -> None:
        self.schedule_days = json.dumps(sorted({int(day) for day in days}))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    # create_all() does not add columns to an existing table. This lightweight
    # migration keeps databases created before starting_week was introduced usable.
    if DATABASE_URL.startswith("sqlite"):
        columns = {column["name"] for column in inspect(engine).get_columns("participants")}
        if "starting_week" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE participants ADD COLUMN starting_week INTEGER NOT NULL DEFAULT 1")
                )


def upsert_participant(
    *,
    person_id: str,
    email: str,
    room_id: str,
    level: int,
    starting_week: int,
    start_date: date,
    schedule_days: Iterable[int],
    reminder_time: str,
) -> Participant:
    """Create or reset a participant's program registration."""

    with SessionLocal() as session:
        participant = session.scalar(
            select(Participant).where(Participant.person_id == person_id)
        )
        if participant is None:
            participant = Participant(person_id=person_id, email=email, room_id=room_id)
            session.add(participant)

        participant.email = email
        participant.room_id = room_id
        participant.level = level
        participant.starting_week = starting_week
        participant.start_date = start_date
        participant.set_schedule_days(schedule_days)
        participant.reminder_time = reminder_time
        participant.current_week = starting_week
        participant.current_day = 1
        participant.is_active = True
        session.commit()
        session.refresh(participant)
        return participant


def list_active_participants() -> list[Participant]:
    with SessionLocal() as session:
        return list(
            session.scalars(
                select(Participant).where(Participant.is_active.is_(True))
            ).all()
        )


def advance_participant(person_id: str) -> bool:
    """Advance one session; return False if the participant was already complete."""

    with SessionLocal() as session:
        participant = session.scalar(
            select(Participant).where(Participant.person_id == person_id)
        )
        if participant is None or not participant.is_active:
            return False

        if participant.current_week == 6 and participant.current_day == 3:
            participant.is_active = False
        elif participant.current_day == 3:
            participant.current_week += 1
            participant.current_day = 1
        else:
            participant.current_day += 1
        session.commit()
        return True


def deactivate_participant(person_id: str) -> None:
    with SessionLocal() as session:
        participant = session.scalar(
            select(Participant).where(Participant.person_id == person_id)
        )
        if participant is not None:
            participant.is_active = False
            session.commit()
