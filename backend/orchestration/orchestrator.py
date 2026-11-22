import uuid
import datetime
import time
from typing import Dict, Any, Optional

from backend.agents.intake_agent import IntakeAgent
from backend.agents.records_memory_agent import RecordsMemoryAgent
from backend.agents.safety_gate_agent import SafetyGateAgent
from backend.agents.triage_router_agent import TriageRouterAgent
from backend.agents.information_agent import InformationAgent
from backend.agents.appointment_agent import AppointmentAgent
from backend.orchestration.tracer import OrchestrationTracer
from backend.database import SessionLocal
from backend.models.intake import IntakeSession
from backend.models.routing import RoutingRecord
from backend.config import settings

class HospitalIntakeOrchestrator:
    """
    Central Multi-Agent Orchestrator.
    Coordinates all 6 Semantic Kernel agents in the Routing with RAG Architecture.
    Enforces Safety Gate non-bypassable priority and maintains execution traces.
    """

    def __init__(self):
        # Initialize the 6 specialized agents
        self.intake_agent = IntakeAgent()
        self.records_memory_agent = RecordsMemoryAgent()
        self.safety_gate_agent = SafetyGateAgent()
        self.triage_router_agent = TriageRouterAgent()
        self.information_agent = InformationAgent()
        self.appointment_agent = AppointmentAgent()

    def process_intake(self, intake_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the full multi-agent orchestration lifecycle.
        """
        pipeline_start = time.time()
        tracer = OrchestrationTracer()

        # Step 1: INTAKE AGENT
        intake_exec_id = f"exec-intake-{uuid.uuid4().hex[:6]}"
        tracer.start_agent_step(
            agent_name="Intake Agent",
            execution_id=intake_exec_id,
            input_summary=f"Patient: {intake_payload.get('patient_name')}, Age: {intake_payload.get('age')}"
        )
        t0 = time.time()
        intake_res = self.intake_agent.run(raw_input=intake_payload, execution_id=intake_exec_id)
        d_intake = (time.time() - t0) * 1000

        if not intake_res["success"]:
            tracer.complete_agent_step(
                agent_name="Intake Agent",
                execution_id=intake_exec_id,
                status="Failed",
                tools_executed=["validate_patient_input"],
                output_summary="Input validation failed",
                duration_ms=d_intake,
                error_details="; ".join(intake_res.get("errors", ["Validation error"]))
            )
            return {
                "success": False,
                "session_id": None,
                "errors": intake_res.get("errors", ["Intake validation error"]),
                "agent_traces": tracer.get_traces(),
                "disclaimer": settings.MANDATORY_DISCLAIMER
            }

        patient_record = intake_res["data"]
        session_id = patient_record["session_id"]
        patient_id = patient_record["patient_id"]
        patient_name = patient_record["patient_name"]
        age = patient_record["age"]
        described_concern = patient_record["described_concern"]
        duration = patient_record.get("duration", "Unspecified")
        tracer.session_id = session_id

        tracer.complete_agent_step(
            agent_name="Intake Agent",
            execution_id=intake_exec_id,
            status="Completed",
            tools_executed=intake_res.get("tools_executed", ["validate_patient_input", "create_patient_record"]),
            output_summary=f"Record created: {session_id} (Patient {patient_id})",
            duration_ms=d_intake
        )

        # Step 2: RECORDS MEMORY AGENT (Team of 3 Mandatory Agent)
        memory_exec_id = f"exec-memory-{uuid.uuid4().hex[:6]}"
        tracer.start_agent_step(
            agent_name="Records Memory Agent",
            execution_id=memory_exec_id,
            input_summary=f"Search history for {patient_name} ({patient_id})"
        )
        t0 = time.time()
        memory_res = self.records_memory_agent.run(
            patient_id=patient_id,
            patient_name=patient_name,
            is_returning_claimed=patient_record.get("is_returning_patient", False),
            execution_id=memory_exec_id,
            session_id=session_id
        )
        d_mem = (time.time() - t0) * 1000
        mem_data = memory_res.get("data", {})

        tracer.complete_agent_step(
            agent_name="Records Memory Agent",
            execution_id=memory_exec_id,
            status="Completed" if memory_res["success"] else "Failed",
            tools_executed=memory_res.get("tools_executed", ["search_patient_history"]),
            output_summary=(
                f"Returning history found: previously visited {mem_data.get('previous_department')}"
                if mem_data.get("is_returning")
                else "First-time patient intake"
            ),
            duration_ms=d_mem,
            error_details="; ".join(memory_res.get("errors", [])) if not memory_res["success"] else None
        )

        # Step 3: SAFETY GATE (Mandatory, Non-bypassable)
        safety_exec_id = f"exec-safety-{uuid.uuid4().hex[:6]}"
        tracer.start_agent_step(
            agent_name="Safety Gate Agent",
            execution_id=safety_exec_id,
            input_summary=f"Screening concern: '{described_concern[:60]}...'"
        )
        t0 = time.time()
        safety_res = self.safety_gate_agent.run(
            described_concern=described_concern,
            patient_name=patient_name,
            age=age,
            additional_info=intake_payload.get("additional_info", ""),
            execution_id=safety_exec_id,
            session_id=session_id
        )
        d_safe = (time.time() - t0) * 1000

        is_urgent = safety_res.get("is_urgent", False)
        tracer.complete_agent_step(
            agent_name="Safety Gate Agent",
            execution_id=safety_exec_id,
            status="Stopped for safety" if is_urgent else "Completed",
            tools_executed=safety_res.get("tools_executed", ["detect_urgent_warning_signs"]),
            output_summary=(
                f"SAFETY STOP: Detected {len(safety_res.get('warning_signs', []))} critical indicators"
                if is_urgent
                else "Safety clearance: No acute red flags detected"
            ),
            duration_ms=d_safe
        )

        # Handle URGENT SAFETY STOP
        if is_urgent:
            # Persist safety stop into database
            db = SessionLocal()
            try:
                db_session = db.query(IntakeSession).filter(IntakeSession.session_id == session_id).first()
                if db_session:
                    db_session.status = "URGENT_STOP"

                urgent_routing = RoutingRecord(
                    session_id=session_id,
                    patient_id=patient_id,
                    selected_department="Emergency Department",
                    department_code="EMERG",
                    confidence_score=1.0,
                    reason=f"Emergency safety stop triggered. Critical warning signs detected: {', '.join(safety_res.get('warning_signs', []))}",
                    alternative_department=None,
                    safety_status="URGENT_STOP",
                    advisory_notes=safety_res.get("advisory"),
                    created_at=datetime.datetime.now(datetime.timezone.utc)
                )
                db.add(urgent_routing)
                db.commit()
            except Exception as e:
                db.rollback()
                print(f"[ORCHESTRATOR DB ERROR] Failed saving urgent stop: {e}")
            finally:
                db.close()

            # Mark remaining agents as skipped for safety
            for pending_agent in ["Triage Router Agent", "Information Agent", "Appointment Agent"]:
                tracer.traces.append({
                    "agent_name": pending_agent,
                    "execution_id": f"skipped-{uuid.uuid4().hex[:6]}",
                    "status": "Stopped for safety",
                    "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "completed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "duration_ms": 0.0,
                    "tools_executed": [],
                    "input_summary": "Skipped due to prior Safety Gate emergency stop",
                    "output_summary": "Routing halted for patient safety",
                    "error_details": None
                })

            return {
                "success": True,
                "session_id": session_id,
                "patient_id": patient_id,
                "patient_name": patient_name,
                "age": age,
                "described_concern": described_concern,
                "safety_status": "URGENT_STOP",
                "is_urgent": True,
                "urgent_warning_signs": safety_res.get("warning_signs", []),
                "urgent_care_advisory": safety_res.get("advisory"),
                "selected_department": "Emergency Department",
                "department_code": "EMERG",
                "confidence_score": 1.0,
                "routing_reason": "Acute emergency warning signs identified. Immediate in-person medical care is required.",
                "alternative_department": None,
                "department_description": "Emergency Department (Walk-In Resuscitation & Trauma Care). Open 24/7.",
                "intake_instructions": "Report directly to Emergency Bay on the Ground Floor or call emergency services (112 / 911 / 108).",
                "documents_required": ["Any available identification and emergency contacts (medical stabilization takes precedence)"],
                "preparation_instructions": ["Do not drive yourself", "Do not delay for paperwork", "Seek emergency assistance immediately"],
                "source_references": [
                    {
                        "document_name": "emergency.txt",
                        "section": "2. Registration & Intake Instructions",
                        "snippet": "NO ADVANCE APPOINTMENT IS REQUIRED OR PERMITTED. Patients are immediately triaged upon arrival."
                    }
                ],
                "available_appointment_slots": [],  # Strictly empty for urgent safety stops!
                "returning_patient_context": {
                    "is_returning": mem_data.get("is_returning", False),
                    "previous_department": mem_data.get("previous_department"),
                    "previous_routing_date": mem_data.get("previous_routing_date"),
                    "previous_concern": mem_data.get("previous_concern"),
                    "reference_note": "Previous routing noted; acute emergency status takes absolute clinical priority."
                },
                "disclaimer": settings.MANDATORY_DISCLAIMER,
                "agent_traces": tracer.get_traces()
            }

        # Step 4: TRIAGE ROUTER AGENT (When Safety check passes)
        triage_exec_id = f"exec-triage-{uuid.uuid4().hex[:6]}"
        tracer.start_agent_step(
            agent_name="Triage Router Agent",
            execution_id=triage_exec_id,
            input_summary=f"Routing concern: '{described_concern[:60]}...'"
        )
        t0 = time.time()
        triage_res = self.triage_router_agent.run(
            described_concern=described_concern,
            age=age,
            duration=duration,
            additional_info=intake_payload.get("additional_info", ""),
            execution_id=triage_exec_id,
            session_id=session_id
        )
        d_triage = (time.time() - t0) * 1000
        triage_data = triage_res["data"]

        tracer.complete_agent_step(
            agent_name="Triage Router Agent",
            execution_id=triage_exec_id,
            status="Completed" if triage_res["success"] else "Failed",
            tools_executed=triage_res.get("tools_executed", ["classify_patient_concern", "get_department_information"]),
            output_summary=f"Selected {triage_data['selected_department']} (Confidence: {triage_data['confidence_score']})",
            duration_ms=d_triage
        )

        selected_dept_name = triage_data["selected_department"]
        dept_code = triage_data["department_code"]

        # Step 5: INFORMATION AGENT (RAG Retrieval)
        info_exec_id = f"exec-info-{uuid.uuid4().hex[:6]}"
        tracer.start_agent_step(
            agent_name="Information Agent",
            execution_id=info_exec_id,
            input_summary=f"RAG retrieval for {selected_dept_name} ({dept_code})"
        )
        t0 = time.time()
        info_res = self.information_agent.run(
            department_name=selected_dept_name,
            department_code=dept_code,
            described_concern=described_concern,
            execution_id=info_exec_id,
            session_id=session_id
        )
        d_info = (time.time() - t0) * 1000
        info_data = info_res["data"]

        tracer.complete_agent_step(
            agent_name="Information Agent",
            execution_id=info_exec_id,
            status="Completed" if info_res["success"] else "Failed",
            tools_executed=info_res.get("tools_executed", ["retrieve_department_information", "format_grounded_instructions"]),
            output_summary=f"Grounded instructions retrieved with {len(info_data.get('source_references', []))} source citations",
            duration_ms=d_info
        )

        # Step 6: APPOINTMENT AGENT (Demonstration Slot Availability)
        appt_exec_id = f"exec-appt-{uuid.uuid4().hex[:6]}"
        tracer.start_agent_step(
            agent_name="Appointment Agent",
            execution_id=appt_exec_id,
            input_summary=f"Querying slots for {dept_code}"
        )
        t0 = time.time()
        appt_res = self.appointment_agent.run(
            department_code=dept_code,
            execution_id=appt_exec_id,
            session_id=session_id
        )
        d_appt = (time.time() - t0) * 1000
        appt_data = appt_res.get("data", {})

        tracer.complete_agent_step(
            agent_name="Appointment Agent",
            execution_id=appt_exec_id,
            status="Completed" if appt_res["success"] else "Failed",
            tools_executed=appt_res.get("tools_executed", ["get_available_appointment_slots"]),
            output_summary=f"Offered {appt_data.get('total_available', 0)} slots for {selected_dept_name}",
            duration_ms=d_appt
        )

        # Persist Final Routing Record
        db = SessionLocal()
        try:
            db_session = db.query(IntakeSession).filter(IntakeSession.session_id == session_id).first()
            if db_session:
                db_session.status = "ROUTED"

            record = RoutingRecord(
                session_id=session_id,
                patient_id=patient_id,
                selected_department=selected_dept_name,
                department_code=dept_code,
                confidence_score=triage_data["confidence_score"],
                reason=triage_data["reason"],
                alternative_department=triage_data.get("alternative_department"),
                safety_status="NORMAL",
                advisory_notes="Routine intake completed; recommended scheduling an evaluation.",
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )
            db.add(record)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[ORCHESTRATOR DB ERROR] Saving routing record: {e}")
        finally:
            db.close()

        # Build full structured response
        return {
            "success": True,
            "session_id": session_id,
            "patient_id": patient_id,
            "patient_name": patient_name,
            "age": age,
            "described_concern": described_concern,
            "safety_status": "NORMAL",
            "is_urgent": False,
            "urgent_warning_signs": [],
            "urgent_care_advisory": None,
            "selected_department": selected_dept_name,
            "department_code": dept_code,
            "confidence_score": triage_data["confidence_score"],
            "routing_reason": triage_data["reason"],
            "alternative_department": triage_data.get("alternative_department"),
            "department_description": info_data.get("department_description"),
            "intake_instructions": info_data.get("intake_instructions"),
            "documents_required": info_data.get("documents_required", []),
            "preparation_instructions": info_data.get("preparation_instructions", []),
            "source_references": info_data.get("source_references", []),
            "available_appointment_slots": appt_data.get("slots", []),
            "returning_patient_context": {
                "is_returning": mem_data.get("is_returning", False),
                "previous_department": mem_data.get("previous_department"),
                "previous_routing_date": mem_data.get("previous_routing_date"),
                "previous_concern": mem_data.get("previous_concern"),
                "reference_note": mem_data.get("reference_note")
            },
            "disclaimer": settings.MANDATORY_DISCLAIMER,
            "agent_traces": tracer.get_traces()
        }

# Global singleton orchestrator
orchestrator = HospitalIntakeOrchestrator()
