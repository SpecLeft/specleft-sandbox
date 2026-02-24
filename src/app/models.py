from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Rule(Base):
    __tablename__ = "rules"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    event_type: Mapped[str] = mapped_column(String, index=True)

    conditions: Mapped[list[Condition]] = relationship(
        "Condition",
        back_populates="rule",
        cascade="all, delete-orphan",
    )
    channels: Mapped[list[Channel]] = relationship(
        "Channel",
        back_populates="rule",
        cascade="all, delete-orphan",
    )
    dispatch_records: Mapped[list[DispatchRecord]] = relationship(
        "DispatchRecord",
        back_populates="rule",
        cascade="all, delete-orphan",
    )


class Condition(Base):
    __tablename__ = "conditions"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    rule_id: Mapped[str] = mapped_column(
        String, ForeignKey("rules.id", ondelete="CASCADE")
    )
    field: Mapped[str] = mapped_column(String)
    operator: Mapped[str] = mapped_column(String)
    value: Mapped[str] = mapped_column(String)

    rule: Mapped[Rule] = relationship("Rule", back_populates="conditions")


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    rule_id: Mapped[str] = mapped_column(
        String, ForeignKey("rules.id", ondelete="CASCADE")
    )
    type: Mapped[str] = mapped_column(String)
    config: Mapped[dict] = mapped_column(JSON, default=dict)

    rule: Mapped[Rule] = relationship("Rule", back_populates="channels")


class DispatchRecord(Base):
    __tablename__ = "dispatch_records"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    rule_id: Mapped[str] = mapped_column(
        String, ForeignKey("rules.id", ondelete="CASCADE"), index=True
    )
    channel_type: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    dispatched_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    rule: Mapped[Rule] = relationship("Rule", back_populates="dispatch_records")
