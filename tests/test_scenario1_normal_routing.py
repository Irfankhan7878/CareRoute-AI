import pytest

def test_scenario1_normal_patient_routing(client):
    """
    SCENARIO 1: NORMAL PATIENT ROUTING
    Input: "I have knee pain for three days."
    Expected:
    - Patient record created.
    - Memory check performed.
    - Safety Gate evaluated.
    - Appropriate department selected (Orthopaedics).
    - RAG instructions retrieved.
    - Appointment slots offered.
    """
    payload = {
        "patient_name": "Marcus Aurelius",
        "age": 42,
        "described_concern": "I have knee pain for three days",
        "duration": "3 days",
        "additional_info": "Mild swelling after running, no trauma.",
        "is_returning_patient": False
    }

    response = client.post("/api/process", json=payload)
    assert response.status_code == 200, f"Expected 200 OK, got: {response.text}"

    data = response.json()

    # 1. Verify Patient Record Created
    assert data["session_id"] is not None
    assert data["session_id"].startswith("INTK-")
    assert data["patient_id"] is not None
    assert data["patient_name"] == "Marcus Aurelius"
    assert data["age"] == 42

    # 2. Verify Safety Gate Evaluation (Routine/Normal)
    assert data["safety_status"] == "NORMAL"
    assert data["is_urgent"] is False
    assert len(data["urgent_warning_signs"]) == 0
    assert data["urgent_care_advisory"] is None

    # 3. Verify Appropriate Department Selected (Orthopaedics)
    assert data["selected_department"] == "Orthopaedics"
    assert data["department_code"] == "ORTHO"
    assert data["confidence_score"] >= 0.70
    assert "knee" in data["routing_reason"].lower() or "musculoskeletal" in data["routing_reason"].lower()

    # 4. Verify RAG Grounded Instructions & Source Citations
    assert data["intake_instructions"] is not None
    assert len(data["documents_required"]) > 0
    assert len(data["preparation_instructions"]) > 0
    assert len(data["source_references"]) > 0
    # Must attribute to orthopaedics.txt or hospital docs
    assert any("orthopaedics.txt" in ref["document_name"] for ref in data["source_references"])

    # 5. Verify Appointment Slots Offered
    assert isinstance(data["available_appointment_slots"], list)
    assert len(data["available_appointment_slots"]) > 0
    for slot in data["available_appointment_slots"]:
        assert slot["department_code"] == "ORTHO"
        assert slot["is_available"] is True

    # 6. Verify Agent Traces Include All Agents
    traces = data["agent_traces"]
    assert len(traces) == 6
    agent_names = [t["agent_name"] for t in traces]
    assert "Intake Agent" in agent_names
    assert "Records Memory Agent" in agent_names
    assert "Safety Gate Agent" in agent_names
    assert "Triage Router Agent" in agent_names
    assert "Information Agent" in agent_names
    assert "Appointment Agent" in agent_names

    # 7. Verify Mandatory Professional Disclaimer Present
    assert "qualified healthcare professional" in data["disclaimer"].lower()
