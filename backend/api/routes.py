import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import (
    Department, Patient, IntakeSession, RoutingRecord,
    AppointmentSlot, AppointmentBooking, AgentExecution, AgentToolLog
)
from backend.schemas import (
    IntakeRequest, IntakeResponse, RoutingResponse,
    AppointmentSlotResponse, BookAppointmentRequest, BookAppointmentResponse,
    AdminDashboardResponse, AgentExecutionSummary
)
from backend.orchestration.orchestrator import orchestrator
from backend.agents.appointment_agent import AppointmentAgent
from backend.config import settings

api_router = APIRouter(prefix="/api")

# 1. POST /api/intake - Validate & create initial intake record
@api_router.post("/intake", response_model=IntakeResponse, status_code=status.HTTP_201_CREATED)
def create_intake(request: IntakeRequest, db: Session = Depends(get_db)):
    """Validates patient intake and stores intake session."""
    payload = request.model_dump()
    res = orchestrator.intake_agent.run(raw_input=payload)
    if not res["success"]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"errors": res.get("errors", ["Invalid intake input."])}
        )
    data = res["data"]
    db_session = db.query(IntakeSession).filter(IntakeSession.session_id == data["session_id"]).first()
    return IntakeResponse(
        session_id=data["session_id"],
        patient_id=data["patient_id"],
        patient_name=data["patient_name"],
        age=data["age"],
        described_concern=data["described_concern"],
        duration=data["duration"],
        is_returning_patient=data["is_returning_patient"],
        status=data["status"],
        created_at=db_session.created_at if db_session else datetime.datetime.now(datetime.timezone.utc)
    )

# 2. POST /api/process - Complete Multi-Agent Workflow
@api_router.post("/process", response_model=RoutingResponse, status_code=status.HTTP_200_OK)
def process_pipeline(request: IntakeRequest):
    """Executes the full multi-agent orchestration pipeline across all 6 agents."""
    payload = request.model_dump()
    result = orchestrator.process_intake(intake_payload=payload)
    if not result.get("success") and not result.get("is_urgent"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"errors": result.get("errors", ["Orchestration failure"])}
        )
    return result

# 3. GET /api/departments - Department Catalogue
@api_router.get("/departments", status_code=status.HTTP_200_OK)
def get_departments(db: Session = Depends(get_db)):
    """Lists all active hospital clinical departments."""
    depts = db.query(Department).all()
    return [
        {
            "id": d.id,
            "code": d.code,
            "name": d.name,
            "description": d.description,
            "location": d.location,
            "operating_hours": d.operating_hours,
            "contact_phone": d.contact_phone
        }
        for d in depts
    ]

# 4. GET /api/departments/{department_id} - Department Details
@api_router.get("/departments/{department_id}", status_code=status.HTTP_200_OK)
def get_department_detail(department_id: str, db: Session = Depends(get_db)):
    """Retrieves department details by numeric ID or departmental code."""
    query = db.query(Department)
    if department_id.isdigit():
        dept = query.filter(Department.id == int(department_id)).first()
    else:
        dept = query.filter(
            (Department.code == department_id.upper()) | (Department.name.ilike(department_id))
        ).first()

    if not dept:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Department '{department_id}' not found.")

    return {
        "id": dept.id,
        "code": dept.code,
        "name": dept.name,
        "description": dept.description,
        "location": dept.location,
        "operating_hours": dept.operating_hours,
        "contact_phone": dept.contact_phone
    }

# 5. GET /api/appointments/available - Available Slots
@api_router.get("/appointments/available", status_code=status.HTTP_200_OK)
def get_available_appointments(
    department_code: str = Query(..., description="Department code (e.g., ORTHO, CARDIO)"),
    date: Optional[str] = Query(None, description="Optional target date in YYYY-MM-DD format"),
    db: Session = Depends(get_db)
):
    """Retrieves demonstration appointment slots filtered by department and date."""
    query = db.query(AppointmentSlot).filter(
        AppointmentSlot.department_code == department_code.upper(),
        AppointmentSlot.is_available == True
    )
    if date:
        query = query.filter(AppointmentSlot.date == date)

    slots = query.order_by(AppointmentSlot.date.asc(), AppointmentSlot.time_slot.asc()).limit(30).all()
    return [
        {
            "id": s.id,
            "department_code": s.department_code,
            "date": s.date,
            "time_slot": s.time_slot,
            "doctor_name": s.doctor_name,
            "is_available": s.is_available
        }
        for s in slots
    ]

# 6. POST /api/appointments/book - Reserve Appointment Slot
@api_router.post("/appointments/book", response_model=BookAppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment(booking_req: BookAppointmentRequest):
    """Atomically reserves an appointment slot, preventing conflict/double booking."""
    appt_agent = AppointmentAgent()
    res = appt_agent.book(
        slot_id=booking_req.slot_id,
        patient_id=booking_req.patient_id,
        patient_name=booking_req.patient_name
    )
    if not res["success"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=res.get("message", "Unable to book appointment.")
        )
    return res

# 7. GET /api/patients/{patient_id}/history - Historical Routing Records
@api_router.get("/patients/{patient_id}/history", status_code=status.HTTP_200_OK)
def get_patient_history(patient_id: str, db: Session = Depends(get_db)):
    """Retrieves past sessions and routing history for a specific patient."""
    patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient {patient_id} not found.")

    sessions = db.query(IntakeSession).filter(
        IntakeSession.patient_id == patient_id
    ).order_by(IntakeSession.created_at.desc()).all()

    routings = db.query(RoutingRecord).filter(
        RoutingRecord.patient_id == patient_id
    ).order_by(RoutingRecord.created_at.desc()).all()

    return {
        "patient_id": patient.patient_id,
        "patient_name": patient.full_name,
        "age": patient.age,
        "registered_at": patient.created_at,
        "intake_sessions": [
            {
                "session_id": s.session_id,
                "described_concern": s.described_concern,
                "duration": s.duration,
                "status": s.status,
                "created_at": s.created_at
            }
            for s in sessions
        ],
        "routing_history": [
            {
                "session_id": r.session_id,
                "selected_department": r.selected_department,
                "department_code": r.department_code,
                "confidence_score": r.confidence_score,
                "reason": r.reason,
                "safety_status": r.safety_status,
                "created_at": r.created_at
            }
            for r in routings
        ]
    }

# 8. GET /api/agents/status - Live Agents & Tools Capability Roster
@api_router.get("/agents/status", status_code=status.HTTP_200_OK)
def get_agents_status():
    """Returns the operational capability status and tools of all 6 agents."""
    return {
        "framework": "Microsoft Semantic Kernel (v1.47.0)",
        "status": "OPERATIONAL",
        "total_agents": 6,
        "agents": [
            {
                "name": "Intake Agent",
                "role": "Input validation and structured intake record creation",
                "tools": ["validate_patient_input", "create_patient_record"],
                "status": "ONLINE"
            },
            {
                "name": "Records Memory Agent",
                "role": "Returning patient historical identification and routing recall",
                "tools": ["search_patient_history", "recall_previous_routing"],
                "status": "ONLINE"
            },
            {
                "name": "Safety Gate Agent",
                "role": "Mandatory red-flag emergency detection and routing halt",
                "tools": ["detect_urgent_warning_signs", "generate_urgent_care_advisory"],
                "status": "ONLINE"
            },
            {
                "name": "Triage Router Agent",
                "role": "Clinical symptom classification and hospital department matching",
                "tools": ["classify_patient_concern", "get_department_information"],
                "status": "ONLINE"
            },
            {
                "name": "Information Agent",
                "role": "Grounded ChromaDB semantic RAG retrieval and intake instructions",
                "tools": ["retrieve_department_information", "format_grounded_instructions"],
                "status": "ONLINE"
            },
            {
                "name": "Appointment Agent",
                "role": "Demonstration slot query and atomic booking reservation",
                "tools": ["get_available_appointment_slots", "reserve_appointment_slot"],
                "status": "ONLINE"
            }
        ]
    }

# 9. GET /api/executions/{execution_id} - Inspect Execution Trace
@api_router.get("/executions/{execution_id}", status_code=status.HTTP_200_OK)
def get_execution_trace(execution_id: str, db: Session = Depends(get_db)):
    """Retrieves execution record and tool logs by execution ID."""
    execution = db.query(AgentExecution).filter(AgentExecution.execution_id == execution_id).first()
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Execution ID '{execution_id}' not found.")

    tool_logs = db.query(AgentToolLog).filter(AgentToolLog.execution_id == execution_id).all()
    return {
        "execution_id": execution.execution_id,
        "session_id": execution.session_id,
        "agent_name": execution.agent_name,
        "status": execution.status,
        "started_at": execution.started_at,
        "completed_at": execution.completed_at,
        "duration_ms": execution.duration_ms,
        "input_summary": execution.input_summary,
        "output_summary": execution.output_summary,
        "error_details": execution.error_details,
        "tool_logs": [
            {
                "id": t.id,
                "tool_name": t.tool_name,
                "timestamp": t.timestamp,
                "is_success": t.is_success,
                "input_args": t.input_args,
                "output_result": t.output_result,
                "error_message": t.error_message
            }
            for t in tool_logs
        ]
    }

# 10. GET /api/admin/dashboard - Admin Metrics & Audit Activity
@api_router.get("/admin/dashboard", response_model=AdminDashboardResponse, status_code=status.HTTP_200_OK)
def get_admin_dashboard(db: Session = Depends(get_db)):
    """Aggregates system-wide intake metrics, safety stops, and recent tool logs."""
    total_sessions = db.query(IntakeSession).count()
    completed_routings = db.query(RoutingRecord).filter(RoutingRecord.safety_status == "NORMAL").count()
    urgent_stops = db.query(RoutingRecord).filter(RoutingRecord.safety_status == "URGENT_STOP").count()
    total_bookings = db.query(AppointmentBooking).count()

    recent_execs = db.query(AgentExecution).order_by(AgentExecution.started_at.desc()).limit(10).all()
    recent_tools = db.query(AgentToolLog).order_by(AgentToolLog.timestamp.desc()).limit(15).all()

    # RAG activity from tool logs
    rag_tools = db.query(AgentToolLog).filter(
        AgentToolLog.tool_name.in_(["retrieve_department_information", "format_grounded_instructions"])
    ).order_by(AgentToolLog.timestamp.desc()).limit(10).all()

    return AdminDashboardResponse(
        total_intake_sessions=total_sessions,
        completed_routings=completed_routings,
        urgent_safety_stops=urgent_stops,
        total_appointments_booked=total_bookings,
        recent_executions=[
            AgentExecutionSummary(
                execution_id=e.execution_id,
                session_id=e.session_id,
                agent_name=e.agent_name,
                status=e.status,
                started_at=e.started_at,
                duration_ms=e.duration_ms,
                input_summary=e.input_summary,
                output_summary=e.output_summary,
                error_details=e.error_details
            )
            for e in recent_execs
        ],
        recent_tool_logs=[
            {
                "execution_id": t.execution_id,
                "agent_name": t.agent_name,
                "tool_name": t.tool_name,
                "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                "is_success": t.is_success,
                "error_message": t.error_message
            }
            for t in recent_tools
        ],
        rag_retrieval_activity=[
            {
                "execution_id": r.execution_id,
                "tool_name": r.tool_name,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "input_args": r.input_args,
                "is_success": r.is_success
            }
            for r in rag_tools
        ]
    )

# 11. GET /api/health - Healthcheck
@api_router.get("/health", status_code=status.HTTP_200_OK)
def get_health():
    """System health check endpoint."""
    return {
        "status": "HEALTHY",
        "service": settings.APP_NAME,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "disclaimer": settings.MANDATORY_DISCLAIMER
    }
