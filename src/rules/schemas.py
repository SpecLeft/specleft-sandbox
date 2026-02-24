from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Any
from enum import Enum
import json


class OperatorEnum(str, Enum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    LT = "lt"
    CONTAINS = "contains"


class ChannelTypeEnum(str, Enum):
    WEBHOOK = "webhook"
    EMAIL = "email"
    LOG = "log"


class DispatchStatusEnum(str, Enum):
    SENT = "sent"
    FAILED = "failed"


class ConditionSchema(BaseModel):
    field: str
    operator: OperatorEnum
    value: str


class ChannelSchema(BaseModel):
    type: ChannelTypeEnum
    config: dict = Field(default_factory=dict)


class RuleCreateSchema(BaseModel):
    name: str
    event_type: str
    is_active: bool = True
    conditions: List[ConditionSchema]
    channels: List[ChannelSchema]

    @field_validator("conditions")
    @classmethod
    def validate_conditions(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one condition is required")
        return v

    @field_validator("channels")
    @classmethod
    def validate_channels(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one channel is required")
        return v


class RuleUpdateSchema(BaseModel):
    name: Optional[str] = None
    event_type: Optional[str] = None
    is_active: Optional[bool] = None
    conditions: Optional[List[ConditionSchema]] = None
    channels: Optional[List[ChannelSchema]] = None


class ConditionResponseSchema(BaseModel):
    id: str
    field: str
    operator: str
    value: str

    class Config:
        from_attributes = True


class ChannelResponseSchema(BaseModel):
    id: str
    type: str
    config: dict

    class Config:
        from_attributes = True


class RuleResponseSchema(BaseModel):
    id: str
    name: str
    is_active: bool
    event_type: str
    conditions: List[ConditionResponseSchema] = []
    channels: List[ChannelResponseSchema] = []

    class Config:
        from_attributes = True


class EventSchema(BaseModel):
    type: str
    payload: dict = Field(default_factory=dict)


class EventResponseSchema(BaseModel):
    triggered_rules: List[str]


class DispatchRecordSchema(BaseModel):
    id: str
    rule_id: str
    channel_type: str
    status: str
    error_message: Optional[str] = None
    dispatched_at: str

    class Config:
        from_attributes = True
