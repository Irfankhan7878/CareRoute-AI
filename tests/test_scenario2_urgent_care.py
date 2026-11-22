import pytest

def test_scenario2_urgent_warning_signs(client):
    """
    SCENARIO 2: URGENT WARNING SIGNS
    Input: "I have severe chest pain and difficulty breathing."
    Expected:
    - Intake record created.
    - Safety Gate identifies urgent warning signs.
    - Normal routing stops.
    - Routine appointment booking is not offered as a substitute for emergency care.
    - Urgent-care advisory is displayed.
    - No diagnosis is generated.
    """
    payload = {
        "patient_name": "Edward Norton",
        "age": 58,
        "described_concern": "I have severe chest pain and difficulty breathing",
        "duration": "1 hour",
        "additional_info": "Profuse cold sweat and dizziness",
        "is_returning_patient": False
    }

    response = client.post("/api/process", json=payload)
    assert response.status_code == 200, f"Expected 200 OK, got: {response.text}"

    data = response.json()

    # 1. Verify Intake record created
    assert data["session_id"] is not None
    assert data["session_id"].startswith("INTK-")
    assert data["patient_name"] == "Edward Norton"

    # 2. Verify Safety Gate identifies urgent warning signs
    assert data["safety_status"] == "URGENT_STOP"
    assert data["is_urgent"] is True
    assert len(data["urgent_warning_signs"]) >= 2
    # Check that chest pain and breathing red flags were flagged
    signs_str = " ".join(data["urgent_warning_signs"]).lower()
    assert "chest pain" in signs_str
    assert "breathing" in signs_str

    # 3. Verify Normal Routing Stopped
    assert data["selected_department"] == "Emergency Department"
    assert data["department_code"] == "EMERG"

    # 4. Verify Routine Appointment Booking IS NOT OFFERED
    assert isinstance(data["available_appointment_slots"], list)
    assert len(data["available_appointment_slots"]) == 0, "Emergency cases must NEVER offer routine appointment booking"

    # 5. Verify Urgent-Care Advisory is Displayed
    assert data["urgent_care_advisory"] is not None
    assert "EMERGENCY WARNING" in data["urgent_care_advisory"]
    assert "112" in data["urgent_care_advisory"] or "911" in data["urgent_care_advisory"]

    # 6. Verify No Diagnosis is Generated (Never diagnoses diseases)
    diagnosis_terms = ["myocardial infarction", "angina pectoris", "pneumothorax", "pulmonary embolism", "covid-19"]
    for term in diagnosis_terms:
        assert term not in data["routing_reason"].lower()

    # 7. Verify Safety Gate cannot be bypassed in agent traces
    traces = data["agent_traces"]
    safety_trace = next((t for t in traces if t["agent_name"] == "Safety Gate Agent"), None)
    assert safety_trace is not None
    assert safety_trace["status"] == "Stopped for safety"

    # Verify downstream agents were stopped for safety
    downstream_traces = [t for t in traces if t["agent_name"] in ["Triage Router Agent", "Information Agent", "Appointment Agent"]]
    for dt in downstream_traces:
        assert dt["status"] == "Stopped for safety"

    # 8. Mandatory professional disclaimer
    assert "qualified healthcare professional" in data["disclaimer"].lower()
