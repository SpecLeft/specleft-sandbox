from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from sqlalchemy.orm import Session
import uuid

from src.database.database import get_db
from src.rules.schemas import (
    RuleCreateSchema,
    RuleUpdateSchema,
    RuleResponseSchema,
    EventSchema,
    EventResponseSchema,
    DispatchRecordSchema,
)
from src.rules.service import RuleService

router = APIRouter()


@router.post("/rules", response_model=RuleResponseSchema, status_code=201)
def create_rule(rule_data: RuleCreateSchema, db: Session = Depends(get_db)):
    service = RuleService(db)
    rule, error, status_code = service.create_rule(rule_data)
    if error:
        raise HTTPException(status_code=status_code, detail=error)
    return rule


@router.get("/rules", response_model=list[RuleResponseSchema])
def get_rules(db: Session = Depends(get_db)):
    service = RuleService(db)
    return service.get_all_rules()


@router.get("/rules/{rule_id}", response_model=RuleResponseSchema)
def get_rule(rule_id: str, db: Session = Depends(get_db)):
    service = RuleService(db)
    rule = service.get_rule_by_id(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.patch("/rules/{rule_id}", response_model=RuleResponseSchema)
def update_rule(
    rule_id: str, rule_data: RuleUpdateSchema, db: Session = Depends(get_db)
):
    service = RuleService(db)
    rule, error, status_code = service.update_rule(rule_id, rule_data)
    if error:
        raise HTTPException(status_code=status_code, detail=error)
    return rule


@router.delete("/rules/{rule_id}", status_code=204)
def delete_rule(rule_id: str, db: Session = Depends(get_db)):
    service = RuleService(db)
    success, error, status_code = service.delete_rule(rule_id)
    if error:
        raise HTTPException(status_code=status_code, detail=error)
    return None


@router.post("/events", response_model=EventResponseSchema, status_code=202)
def create_event(
    event_data: EventSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    service = RuleService(db)
    triggered_rules, status_code = service.process_event(
        event_data.type, event_data.payload
    )
    return EventResponseSchema(triggered_rules=triggered_rules)


@router.get("/dispatch-records", response_model=list[DispatchRecordSchema])
def get_dispatch_records(rule_id: str = Query(...), db: Session = Depends(get_db)):
    service = RuleService(db)
    return service.get_dispatch_records(rule_id)
