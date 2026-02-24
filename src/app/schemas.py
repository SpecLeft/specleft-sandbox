from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    HttpUrl,
    TypeAdapter,
    ValidationInfo,
    field_validator,
)


ConditionOperator = Literal["eq", "neq", "gt", "lt", "contains"]
ChannelType = Literal["webhook", "email", "log"]


class ConditionCreate(BaseModel):
    field: str
    operator: ConditionOperator
    value: str


class ChannelConfig(BaseModel):
    url: HttpUrl | None = None
    to: EmailStr | None = None


class ChannelCreate(BaseModel):
    type: ChannelType
    config: dict = Field(default_factory=dict)

    @field_validator("config")
    @classmethod
    def validate_config(cls, value: dict, info: ValidationInfo) -> dict:
        channel_type = info.data.get("type")
        if channel_type == "webhook":
            url = value.get("url")
            if not url:
                raise ValueError("webhook config requires url")
            TypeAdapter(HttpUrl).validate_python(url)
        if channel_type == "email":
            to = value.get("to")
            if not to:
                raise ValueError("email config requires to")
            TypeAdapter(EmailStr).validate_python(to)
        return value


class RuleCreate(BaseModel):
    name: str
    event_type: str
    is_active: bool = True
    conditions: list[ConditionCreate]
    channels: list[ChannelCreate]

    @field_validator("conditions")
    @classmethod
    def require_conditions(cls, value: list[ConditionCreate]) -> list[ConditionCreate]:
        if not value:
            raise ValueError("rule must include at least one condition")
        return value

    @field_validator("channels")
    @classmethod
    def require_channels(cls, value: list[ChannelCreate]) -> list[ChannelCreate]:
        if not value:
            raise ValueError("rule must include at least one channel")
        return value


class RuleUpdate(BaseModel):
    name: str | None = None
    is_active: bool | None = None


class RuleResponse(BaseModel):
    id: str
    name: str
    is_active: bool
    event_type: str
    conditions: list[ConditionCreate]
    channels: list[ChannelCreate]

    model_config = {"from_attributes": True}


class EventPublish(BaseModel):
    type: str
    payload: dict


class EventResponse(BaseModel):
    triggered_rules: list[str]


class DispatchRecordResponse(BaseModel):
    id: str
    rule_id: str
    channel_type: str
    status: Literal["sent", "failed"]
    error_message: str | None
    dispatched_at: datetime

    model_config = {"from_attributes": True}
