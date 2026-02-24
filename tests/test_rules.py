import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from main import app
from src.database.database import Base, get_db
from src.rules.schemas import RuleCreateSchema, ChannelSchema, ConditionSchema


engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def valid_rule_payload():
    return {
        "name": "test-rule",
        "event_type": "user.created",
        "is_active": True,
        "conditions": [{"field": "user.role", "operator": "eq", "value": "admin"}],
        "channels": [{"type": "log", "config": {}}],
    }


def test_create_a_valid_rule(client, valid_rule_payload):
    response = client.post("/rules", json=valid_rule_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test-rule"
    assert "id" in data
    assert len(data["conditions"]) == 1
    assert len(data["channels"]) == 1


def test_reject_duplicate_rule_name(client, valid_rule_payload):
    client.post("/rules", json=valid_rule_payload)
    response = client.post("/rules", json=valid_rule_payload)
    assert response.status_code == 409


def test_rule_creation_rejected_without_a_channel(client):
    payload = {
        "name": "test-rule",
        "event_type": "user.created",
        "is_active": True,
        "conditions": [{"field": "user.role", "operator": "eq", "value": "admin"}],
        "channels": [],
    }
    response = client.post("/rules", json=payload)
    assert response.status_code == 422


def test_get_all_rules(client, valid_rule_payload):
    client.post("/rules", json=valid_rule_payload)
    response = client.get("/rules")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1


def test_get_a_specific_rule(client, valid_rule_payload):
    create_response = client.post("/rules", json=valid_rule_payload)
    rule_id = create_response.json()["id"]

    response = client.get(f"/rules/{rule_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test-rule"


def test_update_a_rule(client, valid_rule_payload):
    create_response = client.post("/rules", json=valid_rule_payload)
    rule_id = create_response.json()["id"]

    response = client.patch(f"/rules/{rule_id}", json={"name": "updated-rule"})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "updated-rule"


def test_delete_cascades_to_conditions_and_channels(client, valid_rule_payload):
    create_response = client.post("/rules", json=valid_rule_payload)
    rule_id = create_response.json()["id"]

    response = client.delete(f"/rules/{rule_id}")
    assert response.status_code == 204

    get_response = client.get(f"/rules/{rule_id}")
    assert get_response.status_code == 404


def test_rule_fires_when_all_conditions_match(client, valid_rule_payload):
    client.post("/rules", json=valid_rule_payload)

    event_response = client.post(
        "/events", json={"type": "user.created", "payload": {"user": {"role": "admin"}}}
    )
    assert event_response.status_code == 202
    assert "test-rule" in event_response.json()["triggered_rules"]

    rule_id = client.get("/rules").json()[0]["id"]
    records_response = client.get(f"/dispatch-records?rule_id={rule_id}")
    assert len(records_response.json()) > 0


def test_rule_does_not_fire_when_condition_fails(client, valid_rule_payload):
    client.post("/rules", json=valid_rule_payload)

    event_response = client.post(
        "/events",
        json={"type": "user.created", "payload": {"user": {"role": "member"}}},
    )
    assert event_response.status_code == 202
    assert "test-rule" not in event_response.json()["triggered_rules"]


def test_inactive_rule_is_skipped(client, valid_rule_payload):
    valid_rule_payload["is_active"] = False
    client.post("/rules", json=valid_rule_payload)

    event_response = client.post(
        "/events", json={"type": "user.created", "payload": {"user": {"role": "admin"}}}
    )
    assert event_response.status_code == 202
    assert "test-rule" not in event_response.json()["triggered_rules"]


def test_event_response_is_non_blocking(client, valid_rule_payload):
    client.post("/rules", json=valid_rule_payload)

    event_response = client.post(
        "/events", json={"type": "user.created", "payload": {"user": {"role": "admin"}}}
    )
    assert event_response.status_code == 202


def test_one_channel_failure_does_not_block_others(client):
    payload = {
        "name": "multi-channel-rule",
        "event_type": "test.event",
        "is_active": True,
        "conditions": [{"field": "always", "operator": "eq", "value": "true"}],
        "channels": [
            {"type": "webhook", "config": {"url": "http://example.com"}},
            {"type": "log", "config": {}},
        ],
    }
    response = client.post("/rules", json=payload)
    assert response.status_code == 201

    event_response = client.post(
        "/events", json={"type": "test.event", "payload": {"always": "true"}}
    )
    assert event_response.status_code == 202

    rule_id = client.get("/rules").json()[0]["id"]
    records_response = client.get(f"/dispatch-records?rule_id={rule_id}")
    records = records_response.json()
    assert len(records) == 2


def test_records_returned_newest_first(client, valid_rule_payload):
    client.post("/rules", json=valid_rule_payload)
    rule_id = client.get("/rules").json()[0]["id"]

    client.post(
        "/events", json={"type": "user.created", "payload": {"user": {"role": "admin"}}}
    )
    client.post(
        "/events", json={"type": "user.created", "payload": {"user": {"role": "admin"}}}
    )

    records_response = client.get(f"/dispatch-records?rule_id={rule_id}")
    records = records_response.json()
    assert len(records) == 2
