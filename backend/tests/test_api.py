"""API endpoint tests using FastAPI TestClient."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["service"] == "voice-action-gate"


def test_list_actions():
    r = client.get("/api/actions")
    assert r.status_code == 200
    data = r.json()
    assert "DELETE_DATABASE" in data
    assert "DEPLOY_APPLICATION" in data
    assert "TRANSFER_FUNDS" in data
    assert data["DELETE_DATABASE"]["risk"] == "HIGH"


def test_turn_ambiguous():
    r = client.post("/api/turn", json={
        "session_id": "test_ambiguous",
        "text": "Delete the old database."
    })
    assert r.status_code == 200
    body = r.json()
    assert body["gate"]["decision"] == "NEEDS_CLARIFICATION"
    assert "database" in body["gate"]["ambiguous"]


def test_turn_missing_param():
    r = client.post("/api/turn", json={
        "session_id": "test_missing",
        "text": "Delete customer_db."
    })
    assert r.status_code == 200
    body = r.json()
    assert body["gate"]["decision"] == "NEEDS_CLARIFICATION"
    assert "environment" in body["gate"]["missing"]


def test_gate_check_direct():
    r = client.post("/api/gate/check", json={
        "action": "DELETE_DATABASE",
        "transcript": "Delete customer_db in production.",
        "parameters": [
            {"name": "database", "value": "customer_db", "quote": "customer_db"},
            {"name": "environment", "value": "production", "quote": "production"},
        ],
    })
    assert r.status_code == 200
    data = r.json()
    assert data["decision"] == "NEEDS_CONFIRMATION"


def test_audit_log_records_turns():
    r = client.post("/api/turn", json={
        "session_id": "test_audit",
        "text": "Delete customer_db."
    })
    assert r.status_code == 200
    audit = client.get("/api/audit").json()
    assert any(e["action"] == "DELETE_DATABASE" for e in audit)


def test_full_journey_via_api():
    sid = "test_full_journey"
    # Step 1: start action
    r1 = client.post("/api/turn", json={"session_id": sid, "text": "Delete customer_db."})
    assert r1.json()["gate"]["decision"] == "NEEDS_CLARIFICATION"

    # Step 2: provide environment
    r2 = client.post("/api/turn", json={"session_id": sid, "text": "Production."})
    assert r2.json()["gate"]["decision"] == "NEEDS_CONFIRMATION"

    # Step 3: generic ack (should fail for HIGH risk)
    r3 = client.post("/api/turn", json={"session_id": sid, "text": "Okay."})
    assert r3.json()["gate"]["decision"] == "NEEDS_CONFIRMATION"

    # Step 4: explicit confirmation
    r4 = client.post("/api/turn", json={"session_id": sid, "text": "Yes, delete it."})
    assert r4.json()["gate"]["decision"] == "AUTHORIZED"
    assert r4.json()["tool_result"]["result"]["simulated"] is True
