import json
from typing import Any, Dict, Optional
from src.rules.models import OperatorEnum


class ConditionEvaluator:
    @staticmethod
    def get_nested_value(payload: Dict[str, Any], path: str) -> Optional[Any]:
        keys = path.split(".")
        value = payload
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value

    @staticmethod
    def evaluate_condition(
        field: str, operator: str, value: str, payload: Dict[str, Any]
    ) -> bool:
        field_value = ConditionEvaluator.get_nested_value(payload, field)

        if field_value is None:
            return False

        try:
            if operator == OperatorEnum.EQ.value:
                return str(field_value) == value
            elif operator == OperatorEnum.NEQ.value:
                return str(field_value) != value
            elif operator == OperatorEnum.GT.value:
                try:
                    return float(field_value) > float(value)
                except (ValueError, TypeError):
                    return False
            elif operator == OperatorEnum.LT.value:
                try:
                    return float(field_value) < float(value)
                except (ValueError, TypeError):
                    return False
            elif operator == OperatorEnum.CONTAINS.value:
                return value in str(field_value)
            else:
                return False
        except Exception:
            return False

    @staticmethod
    def evaluate_all(conditions: list, payload: Dict[str, Any]) -> bool:
        if not conditions:
            return True

        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator")
            value = condition.get("value")
            if not ConditionEvaluator.evaluate_condition(
                field, operator, value, payload
            ):
                return False

        return True
