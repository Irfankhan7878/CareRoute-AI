import pytest
from backend.database import SessionLocal
from backend.models.routing import RoutingRecord
from backend.models.intake import IntakeSession

def test_scenario3_returning_patient_memory(client):
    """
    SCENARIO 3: RETURNING PATIENT
    Expected:
    - Previous patient history retrieved (seeded Eleanor Vance / P-1001).
    - Previous department displayed (Orthopaedics).
    - Previous routing offered as a reference.
    - New assessment remains possible (new symptom: itchy skin rash).
    - Safety Gate independently evaluates the current concern.
    """
    # Ensure Eleanor Vance P-1001 only has the seeded initial record (INTK-9001) before testing
    db = SessionLocal()
    try:
        db.query(RoutingRecord).filter(
            RoutingRecord.patient_id == "P-1001",
            RoutingRecord.session_id != "INTK-9001"
        ).delete()
        db.query(IntakeSession).filter(
            IntakeSession.patient_id == "P-1001",
            IntakeSession.session_id != "INTK-9001"
        ).delete()
        db.commit()
    finally:
        db.close()

    # Eleanor Vance returns, but now with a NEW dermatological complaint
    payload = {
        "patient_name": "Eleanor Vance",
        "patient_id": "P-1001",
        "age": 45,
        "described_concern": "Developing an itchy red skin rash across both forearms",
        "duration": "4 days",
        "additional_info": "Used a new detergent",
        "is_returning_patient": True
    }

    response = client.post("/api/process", json=payload)
    assert response.status_code == 200, f"Expected 200 OK, got: {response.text}"

    data = response.json()

    # 1. Verify Patient Identity Recognized
    assert data["patient_name"] == "Eleanor Vance"
    assert data["patient_id"] == "P-1001"

    # 2. Verify Returning Patient Context Recalled from Memory
    ret_context = data["returning_patient_context"]
    assert ret_context is not None
    assert ret_context["is_returning"] is True
    assert ret_context["previous_department"] == "Orthopaedics"
    assert ret_context["previous_routing_date"] is not None
    assert "knee" in ret_context["previous_concern"].lower()

    # 3. Verify Previous Routing is Offered as Reference, NOT Dictating New Outcome
    # New complaint is a skin rash, so it MUST route to Dermatology, NOT Orthopaedics!
    assert data["selected_department"] == "Dermatology"
    assert data["department_code"] == "DERM"

    # 4. Verify Safety Gate Independently Evaluated Current Concern
    assert data["safety_status"] == "NORMAL"
    assert data["is_urgent"] is False

    # 5. Verify Grounded Instructions Retrieved for New Department (Dermatology)
    assert len(data["source_references"]) > 0
    assert any("dermatology.txt" in s["document_name"] for s in data["source_references"])

    # 6. Verify Records Memory Agent Step in Trace
    memory_trace = next((t for t in data["agent_traces"] if t["agent_name"] == "Records Memory Agent"), None)
    assert memory_trace is not None
    assert memory_trace["status"] == "Completed"
    assert "search_patient_history" in memory_trace["tools_executed"]
    assert "recall_previous_routing" in memory_trace["tools_executed"]

    # 7. Verify Patient History API Endpoint Directly
    hist_resp = client.get(f"/api/patients/{data['patient_id']}/history")
    assert hist_resp.status_code == 200
    hist_data = hist_resp.json()
    assert hist_data["patient_id"] == "P-1001"
    assert len(hist_data["routing_history"]) >= 2  # Prior orthopaedics + new dermatology
