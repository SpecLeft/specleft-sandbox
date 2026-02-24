from __future__ import annotations
import threading

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session, sessionmaker

from app.database import SessionLocal, init_db as init_database
from app.repository import (
    DuplicateRuleNameError,
    RuleNotFoundError,
    RuleRepository,
    build_rule,
)
from app.schemas import (
    DispatchRecordResponse,
    EventPublish,
    EventResponse,
    RuleCreate,
    RuleResponse,
    RuleUpdate,
)
from app.services import ChannelRegistry, ConditionEvaluator, DispatchService


def create_app(
    *,
    session_local: sessionmaker | None = None,
    init_db: bool = True,
    webhook_delay_seconds: float = 0.0,
    fail_webhook_url: str | None = None,
) -> FastAPI:
    app = FastAPI()
    app.state.dispatch_threads = []
    if init_db:
        init_database()

    session_factory = session_local or SessionLocal

    def get_session() -> Session:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    def get_repository(session: Session = Depends(get_session)) -> RuleRepository:
        return RuleRepository(session)

    @app.post(
        "/rules", response_model=RuleResponse, status_code=status.HTTP_201_CREATED
    )
    def create_rule(
        payload: RuleCreate, repository: RuleRepository = Depends(get_repository)
    ):
        rule = build_rule(
            name=payload.name,
            event_type=payload.event_type,
            is_active=payload.is_active,
            conditions=[condition.model_dump() for condition in payload.conditions],
            channels=[channel.model_dump() for channel in payload.channels],
        )
        try:
            created = repository.create_rule(rule)
        except DuplicateRuleNameError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="duplicate rule name"
            )
        return created

    @app.get("/rules", response_model=list[RuleResponse])
    def list_rules(repository: RuleRepository = Depends(get_repository)):
        return repository.list_rules()

    @app.get("/rules/{rule_id}", response_model=RuleResponse)
    def get_rule(rule_id: str, repository: RuleRepository = Depends(get_repository)):
        try:
            return repository.get_rule(rule_id)
        except RuleNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="rule not found"
            )

    @app.patch("/rules/{rule_id}", response_model=RuleResponse)
    def update_rule(
        rule_id: str,
        payload: RuleUpdate,
        repository: RuleRepository = Depends(get_repository),
    ):
        try:
            rule = repository.get_rule(rule_id)
        except RuleNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="rule not found"
            )
        if payload.name is not None:
            rule.name = payload.name
        if payload.is_active is not None:
            rule.is_active = payload.is_active
        try:
            return repository.update_rule(rule)
        except DuplicateRuleNameError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="duplicate rule name"
            )

    @app.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
    def delete_rule(rule_id: str, repository: RuleRepository = Depends(get_repository)):
        try:
            rule = repository.get_rule(rule_id)
        except RuleNotFoundError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="rule not found"
            )
        repository.delete_rule(rule)
        return None

    @app.post(
        "/events", response_model=EventResponse, status_code=status.HTTP_202_ACCEPTED
    )
    def publish_event(
        payload: EventPublish,
        repository: RuleRepository = Depends(get_repository),
    ):
        evaluator = ConditionEvaluator()
        triggered = [
            rule.name
            for rule in repository.list_active_rules_by_event(payload.type)
            if evaluator.evaluate(rule, payload.payload)
        ]

        def evaluate_and_dispatch():
            session = session_factory()
            try:
                dispatch_repository = RuleRepository(session)
                registry = ChannelRegistry(
                    webhook_delay=webhook_delay_seconds,
                    fail_webhook_url=fail_webhook_url,
                )
                dispatch_service = DispatchService(
                    dispatch_repository, evaluator, registry
                )
                dispatch_service.dispatch_for_event(payload.type, payload.payload)
            finally:
                session.close()

        thread = threading.Thread(target=evaluate_and_dispatch, daemon=True)
        app.state.dispatch_threads = [
            existing for existing in app.state.dispatch_threads if existing.is_alive()
        ]
        app.state.dispatch_threads.append(thread)
        thread.start()
        return EventResponse(triggered_rules=triggered)

    @app.get("/dispatch-records", response_model=list[DispatchRecordResponse])
    def list_dispatch_records(
        rule_id: str, repository: RuleRepository = Depends(get_repository)
    ):
        return repository.list_dispatch_records(rule_id)

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
