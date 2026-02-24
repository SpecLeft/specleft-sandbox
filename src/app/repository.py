from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Channel, Condition, DispatchRecord, Rule


class DuplicateRuleNameError(Exception):
    pass


class RuleNotFoundError(Exception):
    pass


class RuleRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_rules(self) -> list[Rule]:
        return list(self._session.scalars(select(Rule)))

    def get_rule(self, rule_id: str) -> Rule:
        rule = self._session.get(Rule, rule_id)
        if not rule:
            raise RuleNotFoundError(rule_id)
        return rule

    def get_rule_by_name(self, name: str) -> Rule | None:
        return self._session.scalar(select(Rule).where(Rule.name == name))

    def create_rule(self, rule: Rule) -> Rule:
        self._session.add(rule)
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise DuplicateRuleNameError from exc
        self._session.refresh(rule)
        return rule

    def update_rule(self, rule: Rule) -> Rule:
        self._session.add(rule)
        try:
            self._session.commit()
        except IntegrityError as exc:
            self._session.rollback()
            raise DuplicateRuleNameError from exc
        self._session.refresh(rule)
        return rule

    def delete_rule(self, rule: Rule) -> None:
        self._session.delete(rule)
        self._session.commit()

    def list_active_rules_by_event(self, event_type: str) -> list[Rule]:
        return list(
            self._session.scalars(
                select(Rule).where(
                    Rule.event_type == event_type, Rule.is_active.is_(True)
                )
            )
        )

    def add_dispatch_record(
        self,
        *,
        rule_id: str,
        channel_type: str,
        status: str,
        error_message: str | None,
        dispatched_at: datetime | None = None,
    ) -> DispatchRecord:
        record = DispatchRecord(
            rule_id=rule_id,
            channel_type=channel_type,
            status=status,
            error_message=error_message,
            dispatched_at=dispatched_at or datetime.now(UTC),
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return record

    def list_dispatch_records(self, rule_id: str) -> list[DispatchRecord]:
        return list(
            self._session.scalars(
                select(DispatchRecord)
                .where(DispatchRecord.rule_id == rule_id)
                .order_by(desc(DispatchRecord.dispatched_at))
            )
        )


def build_rule(
    *,
    name: str,
    event_type: str,
    is_active: bool,
    conditions: Iterable[dict],
    channels: Iterable[dict],
) -> Rule:
    rule = Rule(name=name, event_type=event_type, is_active=is_active)
    rule.conditions = [
        Condition(field=item["field"], operator=item["operator"], value=item["value"])
        for item in conditions
    ]
    rule.channels = [
        Channel(type=item["type"], config=item.get("config", {})) for item in channels
    ]
    return rule
