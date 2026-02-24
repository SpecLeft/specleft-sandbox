import uuid
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

from src.rules.models import DispatchRecord, ChannelTypeEnum, DispatchStatusEnum


class DispatchRecordRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        rule_id: str,
        channel_type: ChannelTypeEnum,
        status: DispatchStatusEnum,
        error_message: Optional[str] = None,
    ) -> DispatchRecord:
        record = DispatchRecord(
            id=str(uuid.uuid4()),
            rule_id=rule_id,
            channel_type=channel_type,
            status=status,
            error_message=error_message,
            dispatched_at=datetime.utcnow(),
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_by_rule_id(self, rule_id: str) -> List[DispatchRecord]:
        return (
            self.db.query(DispatchRecord)
            .filter(DispatchRecord.rule_id == rule_id)
            .order_by(desc(DispatchRecord.dispatched_at))
            .all()
        )
