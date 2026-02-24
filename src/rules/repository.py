import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from src.rules.models import Rule, Condition, Channel


class RuleRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, name: str, event_type: str, is_active: bool = True) -> Rule:
        rule = Rule(
            id=str(uuid.uuid4()),
            name=name,
            event_type=event_type,
            is_active=is_active,
        )
        self.db.add(rule)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get_all(self) -> List[Rule]:
        return self.db.query(Rule).all()

    def get_by_id(self, rule_id: str) -> Optional[Rule]:
        return self.db.query(Rule).filter(Rule.id == rule_id).first()

    def get_by_name(self, name: str) -> Optional[Rule]:
        return self.db.query(Rule).filter(Rule.name == name).first()

    def update(self, rule_id: str, **kwargs) -> Optional[Rule]:
        rule = self.get_by_id(rule_id)
        if not rule:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(rule, key):
                setattr(rule, key, value)
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def delete(self, rule_id: str) -> bool:
        rule = self.get_by_id(rule_id)
        if not rule:
            return False
        self.db.delete(rule)
        self.db.commit()
        return True

    def add_condition(
        self, rule_id: str, field: str, operator: str, value: str
    ) -> Optional[Condition]:
        rule = self.get_by_id(rule_id)
        if not rule:
            return None
        condition = Condition(
            id=str(uuid.uuid4()),
            rule_id=rule_id,
            field=field,
            operator=operator,
            value=value,
        )
        self.db.add(condition)
        self.db.commit()
        self.db.refresh(condition)
        return condition

    def add_channel(
        self, rule_id: str, channel_type: str, config: dict
    ) -> Optional[Channel]:
        rule = self.get_by_id(rule_id)
        if not rule:
            return None
        import json

        channel = Channel(
            id=str(uuid.uuid4()),
            rule_id=rule_id,
            type=channel_type,
            config=json.dumps(config),
        )
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)
        return channel

    def get_active_rules_by_event_type(self, event_type: str) -> List[Rule]:
        return (
            self.db.query(Rule)
            .filter(Rule.is_active == True, Rule.event_type == event_type)
            .all()
        )
