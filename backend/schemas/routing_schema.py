from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import datetime

class GroundedSource(BaseModel):
    document_name: str
    section: Optional[str] = None
    snippet: str

class ReturningPatientContext(BaseModel):
    is_returning: bool
    previous_department: Optional[str] = None
    previous_routing_date: Optional[str] = None
    previous_concern: Optional[str] = None
    reference_note: Optional[str] = None

class AgentTraceStep(BaseModel):
    agent_name: str
    execution_id: str
    status: str
    started_at: str
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None
    tools_executed: List[str] = []
    input_summary: Optional[str] = None
    output_summary: Optional[str] = None
    error_details: Optional[str] = None

class RoutingResponse(BaseModel):
    session_id: str
    patient_id: str
    patient_name: str
    age: int
    described_concern: str
    safety_status: str  # NORMAL, URGENT_STOP
    is_urgent: bool = False
    urgent_warning_signs: List[str] = []
    urgent_care_advisory: Optional[str] = None

    # Triage Routing
    selected_department: Optional[str] = None
    department_code: Optional[str] = None
    confidence_score: Optional[float] = None
    routing_reason: Optional[str] = None
    alternative_department: Optional[str] = None

    # RAG Information
    department_description: Optional[str] = None
    intake_instructions: Optional[str] = None
    documents_required: List[str] = []
    preparation_instructions: List[str] = []
    source_references: List[GroundedSource] = []

    # Appointment Slots
    available_appointment_slots: List[Dict[str, Any]] = []

    # Returning Patient Memory
    returning_patient_context: Optional[ReturningPatientContext] = None

    # Mandatory disclaimer
    disclaimer: str

    # Agent Tracing
    agent_traces: List[AgentTraceStep] = []
