import uuid
import json
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from src.rules.models import Rule, ChannelTypeEnum, DispatchStatusEnum
from src.rules.repository import RuleRepository
from src.rules.schemas import (
    RuleCreateSchema,
    RuleUpdateSchema,
    RuleResponseSchema,
    ConditionResponseSchema,
    ChannelResponseSchema,
)
from src.conditions.evaluator import ConditionEvaluator
from src.channels.dispatcher import dispatch_to_channel, validate_channel_config
from src.dispatch_records.repository import DispatchRecordRepository


class RuleService:
    def __init__(self, db: Session):
        self.db = db
        self.rule_repo = RuleRepository(db)
        self.dispatch_repo = DispatchRecordRepository(db)

    def create_rule(
        self, rule_data: RuleCreateSchema
    ) -> tuple[Optional[RuleResponseSchema], Optional[str], int]:
        existing = self.rule_repo.get_by_name(rule_data.name)
        if existing:
            return None, "Rule with this name already exists", 409

        rule = self.rule_repo.create(
            name=rule_data.name,
            event_type=rule_data.event_type,
            is_active=rule_data.is_active,
        )

        for condition in rule_data.conditions:
            self.rule_repo.add_condition(
                rule_id=rule.id,
                field=condition.field,
                operator=condition.operator.value,
                value=condition.value,
            )

        for channel in rule_data.channels:
            is_valid, error = validate_channel_config(
                channel.type.value, channel.config
            )
            if not is_valid:
                self.db.delete(rule)
                self.db.commit()
                return None, error, 422

            self.rule_repo.add_channel(
                rule_id=rule.id,
                channel_type=channel.type.value,
                config=channel.config,
            )

        return self._to_response(rule), None, 201

    def get_all_rules(self) -> List[RuleResponseSchema]:
        rules = self.rule_repo.get_all()
        return [self._to_response(rule) for rule in rules]

    def get_rule_by_id(self, rule_id: str) -> Optional[RuleResponseSchema]:
        rule = self.rule_repo.get_by_id(rule_id)
        if not rule:
            return None
        return self._to_response(rule)

    def update_rule(
        self, rule_id: str, rule_data: RuleUpdateSchema
    ) -> tuple[Optional[RuleResponseSchema], Optional[str], int]:
        rule = self.rule_repo.get_by_id(rule_id)
        if not rule:
            return None, "Rule not found", 404

        if rule_data.name and rule_data.name != rule.name:
            existing = self.rule_repo.get_by_name(rule_data.name)
            if existing:
                return None, "Rule with this name already exists", 409

        update_data = {}
        if rule_data.name is not None:
            update_data["name"] = rule_data.name
        if rule_data.event_type is not None:
            update_data["event_type"] = rule_data.event_type
        if rule_data.is_active is not None:
            update_data["is_active"] = rule_data.is_active

        if update_data:
            rule = self.rule_repo.update(rule_id, **update_data)

        return self._to_response(rule), None, 200

    def delete_rule(self, rule_id: str) -> tuple[bool, Optional[str], int]:
        success = self.rule_repo.delete(rule_id)
        if not success:
            return False, "Rule not found", 404
        return True, None, 204

    def process_event(self, event_type: str, payload: dict) -> tuple[List[str], int]:
        rules = self.rule_repo.get_active_rules_by_event_type(event_type)
        triggered_rules = []

        for rule in rules:
            conditions = [
                {
                    "field": c.field,
                    "operator": c.operator,
                    "value": c.value,
                }
                for c in rule.conditions
            ]

            if ConditionEvaluator.evaluate_all(conditions, payload):
                triggered_rules.append(rule.name)
                self._dispatch_rule(rule)

        return triggered_rules, 202

    def _dispatch_rule(self, rule: Rule):
        for channel in rule.channels:
            config = json.loads(channel.config) if channel.config else {}
            success, error = dispatch_to_channel(channel.type.value, config)

            status = DispatchStatusEnum.SENT if success else DispatchStatusEnum.FAILED
            self.dispatch_repo.create(
                rule_id=rule.id,
                channel_type=channel.type,
                status=status,
                error_message=error if not success else None,
            )

    def get_dispatch_records(self, rule_id: str) -> List:
        records = self.dispatch_repo.get_by_rule_id(rule_id)
        return [
            {
                "id": str(r.id),
                "rule_id": str(r.rule_id),
                "channel_type": r.channel_type.value,
                "status": r.status.value,
                "error_message": r.error_message,
                "dispatched_at": r.dispatched_at.isoformat(),
            }
            for r in records
        ]

    def _to_response(self, rule: Rule) -> RuleResponseSchema:
        return RuleResponseSchema(
            id=str(rule.id),
            name=rule.name,
            is_active=rule.is_active,
            event_type=rule.event_type,
            conditions=[
                ConditionResponseSchema(
                    id=str(c.id),
                    field=c.field,
                    operator=c.operator.value,
                    value=c.value,
                )
                for c in rule.conditions
            ],
            channels=[
                ChannelResponseSchema(
                    id=str(ch.id),
                    type=ch.type.value,
                    config=json.loads(ch.config) if ch.config else {},
                )
                for ch in rule.channels
            ],
        )
