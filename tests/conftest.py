from __future__ import annotations

import time
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

from app.database import Base
from app.main import create_app


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    try:
        yield engine
    finally:
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(db_engine):
    session_local = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    with session_local() as session:
        yield session


@pytest.fixture()
def client(db_engine):
    session_local = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    app = create_app(
        session_local=session_local,
        init_db=False,
        webhook_delay_seconds=0.3,
        fail_webhook_url="https://fail.example.com",
    )
    with TestClient(app) as test_client:
        yield test_client
    for thread in getattr(app.state, "dispatch_threads", []):
        thread.join(timeout=1.0)


def build_rule_payload(
    *,
    name: str,
    event_type: str,
    conditions: list[dict],
    channels: list[dict],
    is_active: bool = True,
) -> dict:
    return {
        "name": name,
        "event_type": event_type,
        "is_active": is_active,
        "conditions": conditions,
        "channels": channels,
    }


def wait_for_dispatch_records(
    client: TestClient, rule_id: str, expected: int, timeout: float = 1.0
) -> list[dict]:
    start = time.monotonic()
    last_seen: list[dict] = []
    while time.monotonic() - start < timeout:
        response = client.get(f"/dispatch-records?rule_id={rule_id}")
        last_seen = response.json()
        if len(last_seen) >= expected:
            return last_seen
        time.sleep(0.01)
    return last_seen


def assert_no_dispatch_records(
    client: TestClient, rule_id: str, timeout: float = 0.3
) -> None:
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        response = client.get(f"/dispatch-records?rule_id={rule_id}")
        if response.json():
            raise AssertionError("expected no dispatch records")
        time.sleep(0.01)
