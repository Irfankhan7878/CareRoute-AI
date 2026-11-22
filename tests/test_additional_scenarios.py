import pytest

def test_invalid_patient_input(client):
    """Verifies that invalid age and empty concern produce validation errors."""
    # Test 1: Age out of bounds
    invalid_age_payload = {
        "patient_name": "Invalid Patient",
        "age": 140,  # Max is 120
        "described_concern": "Knee pain",
        "duration": "1 day"
    }
    resp1 = client.post("/api/intake", json=invalid_age_payload)
    assert resp1.status_code == 422

    # Test 2: Blank patient concern
    blank_concern_payload = {
        "patient_name": "Invalid Patient",
        "age": 30,
        "described_concern": "   ",
        "duration": "1 day"
    }
    resp2 = client.post("/api/intake", json=blank_concern_payload)
    assert resp2.status_code == 422

def test_low_confidence_ambiguous_routing(client):
    """Verifies that an ambiguous or vague complaint falls back to General Medicine safely."""
    vague_payload = {
        "patient_name": "Ambiguous Case",
        "age": 30,
        "described_concern": "I feel strange and a bit unwell overall without specific location",
        "duration": "1 week",
        "is_returning_patient": False
    }
    response = client.post("/api/process", json=vague_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["selected_department"] == "General Medicine"
    assert data["department_code"] == "GEN_MED"
    assert data["confidence_score"] <= 0.65

import uuid

def test_patient_without_previous_history(client):
    """Verifies that a brand new patient without history is handled correctly."""
    unique_name = f"BrandNewPerson_{uuid.uuid4().hex[:8]}"
    new_patient_payload = {
        "patient_name": unique_name,
        "age": 28,
        "described_concern": "Stomach cramps and acid reflux after meals",
        "duration": "2 days",
        "is_returning_patient": False
    }
    response = client.post("/api/process", json=new_patient_payload)
    assert response.status_code == 200
    data = response.json()
    ret_context = data["returning_patient_context"]
    assert ret_context["is_returning"] is False
    assert ret_context["previous_department"] is None

def test_appointment_booking_and_duplicate_prevention(client):
    """Verifies slot reservation and duplicate double-booking prevention."""
    # 1. Fetch available slots for Gastroenterology
    avail_resp = client.get("/api/appointments/available?department_code=GASTRO")
    assert avail_resp.status_code == 200
    slots = avail_resp.json()
    assert len(slots) > 0

    target_slot = slots[0]
    slot_id = target_slot["id"]

    # 2. Book the slot
    book_req = {
        "slot_id": slot_id,
        "patient_id": "P-TEST-01",
        "patient_name": "First Booker"
    }
    book_resp1 = client.post("/api/appointments/book", json=book_req)
    assert book_resp1.status_code == 201
    book_data = book_resp1.json()
    assert book_data["status"] == "CONFIRMED"
    assert book_data["booking_reference"].startswith("BK-")

    # 3. Attempt duplicate booking for the SAME slot -> must be rejected with 409 Conflict
    book_req2 = {
        "slot_id": slot_id,
        "patient_id": "P-TEST-02",
        "patient_name": "Second Booker"
    }
    book_resp2 = client.post("/api/appointments/book", json=book_req2)
    assert book_resp2.status_code == 409
    assert "already been reserved" in book_resp2.json()["detail"].lower()

def test_agent_status_endpoint(client):
    """Verifies that /api/agents/status lists all 6 agents and their tools."""
    resp = client.get("/api/agents/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_agents"] == 6
    assert len(data["agents"]) == 6
    for agent in data["agents"]:
        assert len(agent["tools"]) >= 2
        assert agent["status"] == "ONLINE"

def test_admin_dashboard_metrics(client):
    """Verifies that /api/admin/dashboard returns valid metrics and execution logs."""
    resp = client.get("/api/admin/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_intake_sessions"] >= 1
    assert "recent_executions" in data
    assert "recent_tool_logs" in data
    assert "rag_retrieval_activity" in data
