from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

from app.models import Rule
from app.repository import RuleRepository


@dataclass(frozen=True)
class DispatchResult:
    status: str
    error_message: str | None = None


class ChannelDispatcher(Protocol):
    def dispatch(self, rule: Rule, channel: dict, payload: dict) -> DispatchResult: ...


class LogDispatcher:
    def dispatch(self, rule: Rule, channel: dict, payload: dict) -> DispatchResult:
        return DispatchResult(status="sent")


class WebhookDispatcher:
    def __init__(
        self, delay_seconds: float = 0.0, fail_on_url: str | None = None
    ) -> None:
        self._delay = delay_seconds
        self._fail_on_url = fail_on_url

    def dispatch(self, rule: Rule, channel: dict, payload: dict) -> DispatchResult:
        url = channel.get("config", {}).get("url")
        if self._delay:
            time.sleep(self._delay)
        if self._fail_on_url and url == self._fail_on_url:
            return DispatchResult(status="failed", error_message="webhook failed")
        return DispatchResult(status="sent")


class EmailDispatcher:
    def dispatch(self, rule: Rule, channel: dict, payload: dict) -> DispatchResult:
        return DispatchResult(status="sent")


class ConditionEvaluator:
    def evaluate(self, rule: Rule, payload: dict) -> bool:
        if not rule.conditions:
            return True
        return all(
            self._evaluate_condition(condition, payload)
            for condition in rule.conditions
        )

    def _evaluate_condition(self, condition, payload: dict) -> bool:
        current = payload
        for part in condition.field.split("."):
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        operator = condition.operator
        value = condition.value
        compare_value = self._coerce_value(current, value)
        if operator == "eq":
            return current == compare_value
        if operator == "neq":
            return current != compare_value
        if operator == "contains":
            if isinstance(current, list):
                return compare_value in current
            if isinstance(current, str):
                return str(compare_value) in current
            return False
        if operator in {"gt", "lt"}:
            if not isinstance(current, (int, float)):
                return False
            try:
                numeric_value = float(value)
            except ValueError:
                return False
            return (
                current > numeric_value if operator == "gt" else current < numeric_value
            )
        return False

    def _coerce_value(self, current, value: str):
        if isinstance(current, bool):
            return value.lower() in {"true", "1", "yes"}
        if isinstance(current, int) and not isinstance(current, bool):
            try:
                return int(value)
            except ValueError:
                return value
        if isinstance(current, float):
            try:
                return float(value)
            except ValueError:
                return value
        if isinstance(current, list) and current:
            first = current[0]
            if isinstance(first, bool):
                return value.lower() in {"true", "1", "yes"}
            if isinstance(first, int) and not isinstance(first, bool):
                try:
                    return int(value)
                except ValueError:
                    return value
            if isinstance(first, float):
                try:
                    return float(value)
                except ValueError:
                    return value
        return value


class ChannelRegistry:
    def __init__(
        self, webhook_delay: float = 0.0, fail_webhook_url: str | None = None
    ) -> None:
        self._registry = {
            "webhook": WebhookDispatcher(
                delay_seconds=webhook_delay, fail_on_url=fail_webhook_url
            ),
            "email": EmailDispatcher(),
            "log": LogDispatcher(),
        }

    def dispatcher_for(self, channel_type: str) -> ChannelDispatcher:
        return self._registry[channel_type]


class DispatchService:
    def __init__(
        self,
        repository: RuleRepository,
        evaluator: ConditionEvaluator,
        registry: ChannelRegistry,
    ) -> None:
        self._repository = repository
        self._evaluator = evaluator
        self._registry = registry

    def dispatch_for_event(self, event_type: str, payload: dict) -> list[str]:
        triggered: list[str] = []
        rules = self._repository.list_active_rules_by_event(event_type)
        for rule in rules:
            if self._evaluator.evaluate(rule, payload):
                triggered.append(rule.name)
                for channel in rule.channels:
                    self._dispatch_channel(rule, channel, payload)
        return triggered

    def _dispatch_channel(self, rule: Rule, channel, payload: dict) -> None:
        dispatcher = self._registry.dispatcher_for(channel.type)
        try:
            result = dispatcher.dispatch(
                rule, {"type": channel.type, "config": channel.config}, payload
            )
        except Exception as exc:  # noqa: BLE001
            result = DispatchResult(status="failed", error_message=str(exc))
        self._repository.add_dispatch_record(
            rule_id=rule.id,
            channel_type=channel.type,
            status=result.status,
            error_message=result.error_message,
        )
