import time
import uuid
import datetime
from typing import Dict, Any, Optional, List
from semantic_kernel.functions import kernel_function
from backend.agents.base_agent import BaseAgent
from backend.database import SessionLocal
from backend.models.patient import Patient
from backend.models.intake import IntakeSession
from backend.models.routing import RoutingRecord

class RecordsMemoryPlugin:
    """
    Microsoft Semantic Kernel Plugin for Records Memory Agent.
    Contains real Python tools for querying historical patient records and previous routing decisions.
    """

    def __init__(self, agent: "RecordsMemoryAgent"):
        self.agent = agent

    @kernel_function(
        name="search_patient_history",
        description="Searches historical intake sessions and records using patient name or unique patient identifier."
    )
    def search_patient_history(
        self,
        patient_name: Optional[str] = None,
        patient_id: Optional[str] = None,
        current_session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Tool 1: Search database for past sessions of this patient excluding the active session."""
        db = SessionLocal()
        try:
            matched_patient = None
            if patient_id:
                matched_patient = db.query(Patient).filter(Patient.patient_id == patient_id).first()
            if not matched_patient and patient_name:
                matched_patient = db.query(Patient).filter(
                    Patient.full_name.ilike(patient_name.strip())
                ).first()

            if not matched_patient:
                return {
                    "has_history": False,
                    "patient_id": patient_id,
                    "patient_name": patient_name,
                    "history_count": 0,
                    "sessions": []
                }

            # Query historical intake sessions, excluding current session
            session_query = db.query(IntakeSession).filter(
                IntakeSession.patient_id == matched_patient.patient_id
            )
            if current_session_id:
                session_query = session_query.filter(IntakeSession.session_id != current_session_id)
            
            sessions = session_query.order_by(IntakeSession.created_at.desc()).all()

            # Also check if prior routing records exist
            routing_query = db.query(RoutingRecord).filter(
                RoutingRecord.patient_id == matched_patient.patient_id
            )
            if current_session_id:
                routing_query = routing_query.filter(RoutingRecord.session_id != current_session_id)
            prior_routings = routing_query.count()

            session_list = [
                {
                    "session_id": s.session_id,
                    "described_concern": s.described_concern,
                    "duration": s.duration,
                    "created_at": s.created_at.strftime("%Y-%m-%d %H:%M UTC") if s.created_at else None,
                    "status": s.status
                }
                for s in sessions
            ]

            has_history = len(session_list) > 0 or prior_routings > 0

            return {
                "has_history": has_history,
                "patient_id": matched_patient.patient_id,
                "patient_name": matched_patient.full_name,
                "history_count": len(session_list),
                "sessions": session_list
            }
        finally:
            db.close()

    @kernel_function(
        name="recall_previous_routing",
        description="Retrieves the most recent hospital department routing details, date, and reason for a patient."
    )
    def recall_previous_routing(
        self,
        patient_id: str,
        current_session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Tool 2: Extract latest department routing record for returning patient reference."""
        if not patient_id:
            return {
                "found": False,
                "message": "No patient ID provided for routing recall."
            }

        db = SessionLocal()
        try:
            routing_query = db.query(RoutingRecord).filter(
                RoutingRecord.patient_id == patient_id
            )
            if current_session_id:
                routing_query = routing_query.filter(RoutingRecord.session_id != current_session_id)

            recent_routing = routing_query.order_by(RoutingRecord.created_at.desc()).first()

            if not recent_routing:
                return {
                    "found": False,
                    "patient_id": patient_id,
                    "message": "No previous routing record found in hospital memory."
                }

            # Retrieve intake concern corresponding to this routing
            matching_session = db.query(IntakeSession).filter(
                IntakeSession.session_id == recent_routing.session_id
            ).first()

            routing_date = recent_routing.created_at.strftime("%Y-%m-%d") if recent_routing.created_at else "Unknown"

            return {
                "found": True,
                "patient_id": patient_id,
                "session_id": recent_routing.session_id,
                "previous_department": recent_routing.selected_department,
                "department_code": recent_routing.department_code,
                "confidence_score": recent_routing.confidence_score,
                "previous_routing_date": routing_date,
                "previous_concern": matching_session.described_concern if matching_session else "Unspecified prior concern",
                "previous_reason": recent_routing.reason,
                "reference_advisory": (
                    f"Returning patient identified. Previous visit on {routing_date} was routed to "
                    f"{recent_routing.selected_department}. Note: Current symptoms must be evaluated independently."
                )
            }
        finally:
            db.close()


class RecordsMemoryAgent(BaseAgent):
    """
    Agent 6: Records Memory Agent (Team of 3 Mandatory Agent).
    Checks previous patient history and recalls prior department routings for contextual reference.
    Never assumes old routing dictates current assessment.
    """

    def __init__(self):
        super().__init__(
            agent_name="Records Memory Agent",
            description="Recalls prior hospital visits, intake sessions, and department routings for returning patients."
        )
        self.plugin = RecordsMemoryPlugin(self)
        self.kernel.add_plugin(self.plugin, plugin_name="RecordsMemoryPlugin")

    def run(
        self,
        patient_id: Optional[str],
        patient_name: str,
        is_returning_claimed: bool = False,
        execution_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes history search and routing recall workflow.
        """
        exec_id = execution_id or f"exec-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        self.create_execution_record(
            execution_id=exec_id,
            session_id=session_id,
            input_summary=f"Patient ID: {patient_id}, Name: {patient_name}, Claimed Returning: {is_returning_claimed}"
        )

        try:
            # Step 1: Tool 1 execution - search_patient_history
            history_result = self.plugin.search_patient_history(
                patient_name=patient_name,
                patient_id=patient_id,
                current_session_id=session_id
            )
            self.log_tool_run(
                execution_id=exec_id,
                tool_name="search_patient_history",
                input_args={"patient_name": patient_name, "patient_id": patient_id, "current_session_id": session_id},
                output_result=history_result,
                is_success=True
            )

            resolved_patient_id = history_result.get("patient_id") or patient_id
            recall_result = {"found": False}

            # Step 2: Tool 2 execution - recall_previous_routing (if history exists)
            if history_result["has_history"] and resolved_patient_id:
                recall_result = self.plugin.recall_previous_routing(
                    patient_id=resolved_patient_id,
                    current_session_id=session_id
                )
                self.log_tool_run(
                    execution_id=exec_id,
                    tool_name="recall_previous_routing",
                    input_args={"patient_id": resolved_patient_id, "current_session_id": session_id},
                    output_result=recall_result,
                    is_success=True
                )

            duration_ms = (time.time() - start_time) * 1000
            summary = (
                f"Found returning history for {patient_name} (Prev: {recall_result.get('previous_department')})"
                if recall_result.get("found")
                else f"No prior history found for {patient_name} (First-time intake)"
            )
            self.update_execution_record(
                execution_id=exec_id,
                status="COMPLETED",
                output_summary=summary,
                duration_ms=duration_ms
            )

            return {
                "success": True,
                "execution_id": exec_id,
                "tools_executed": ["search_patient_history", "recall_previous_routing"] if recall_result.get("found") else ["search_patient_history"],
                "data": {
                    "is_returning": bool(history_result["has_history"] or recall_result.get("found")),
                    "resolved_patient_id": resolved_patient_id,
                    "previous_department": recall_result.get("previous_department"),
                    "previous_routing_date": recall_result.get("previous_routing_date"),
                    "previous_concern": recall_result.get("previous_concern"),
                    "reference_note": recall_result.get("reference_advisory") or "First-time patient intake."
                }
            }

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.update_execution_record(
                execution_id=exec_id,
                status="FAILED",
                output_summary="Failed querying patient history",
                duration_ms=duration_ms,
                error_details=str(e)
            )
            return {
                "success": False,
                "execution_id": exec_id,
                "errors": [str(e)],
                "data": {
                    "is_returning": False,
                    "resolved_patient_id": patient_id,
                    "previous_department": None,
                    "previous_routing_date": None,
                    "reference_note": "History lookup unavailable."
                }
            }
