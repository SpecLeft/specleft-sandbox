import uuid
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum

from src.database.database import Base


class OperatorEnum(str, enum.Enum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    LT = "lt"
    CONTAINS = "contains"


class ChannelTypeEnum(str, enum.Enum):
    WEBHOOK = "webhook"
    EMAIL = "email"
    LOG = "log"


class DispatchStatusEnum(str, enum.Enum):
    SENT = "sent"
    FAILED = "failed"


class Rule(Base):
    __tablename__ = "rules"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), unique=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    event_type = Column(String(255), nullable=False)

    conditions = relationship(
        "Condition", back_populates="rule", cascade="all, delete-orphan"
    )
    channels = relationship(
        "Channel", back_populates="rule", cascade="all, delete-orphan"
    )
    dispatch_records = relationship(
        "DispatchRecord", back_populates="rule", cascade="all, delete-orphan"
    )


class Condition(Base):
    __tablename__ = "conditions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String(36), ForeignKey("rules.id"), nullable=False)
    field = Column(String(255), nullable=False)
    operator = Column(SQLEnum(OperatorEnum), nullable=False)
    value = Column(String(255), nullable=False)

    rule = relationship("Rule", back_populates="conditions")


class Channel(Base):
    __tablename__ = "channels"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String(36), ForeignKey("rules.id"), nullable=False)
    type = Column(SQLEnum(ChannelTypeEnum), nullable=False)
    config = Column(String(1000), nullable=False)

    rule = relationship("Rule", back_populates="channels")


class DispatchRecord(Base):
    __tablename__ = "dispatch_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String(36), ForeignKey("rules.id"), nullable=False)
    channel_type = Column(SQLEnum(ChannelTypeEnum), nullable=False)
    status = Column(SQLEnum(DispatchStatusEnum), nullable=False)
    error_message = Column(String(500), nullable=True)
    dispatched_at = Column(DateTime, nullable=False)

    rule = relationship("Rule", back_populates="dispatch_records")
