import uuid
import datetime
import time
from typing import Dict, Any, Optional
from semantic_kernel.functions import kernel_function
from backend.agents.base_agent import BaseAgent
from backend.database import SessionLocal
from backend.models.patient import Patient
from backend.models.intake import IntakeSession

class IntakePlugin:
    """
    Microsoft Semantic Kernel Plugin for Intake Agent.
    Contains real Python tool functions for input validation and record creation.
    """

    def __init__(self, agent: "IntakeAgent"):
        self.agent = agent

    @kernel_function(
        name="validate_patient_input",
        description="Validates patient details including name, age range (0-120), and symptom concern completeness."
    )
    def validate_patient_input(
        self,
        patient_name: str,
        age: int,
        described_concern: str,
        duration: Optional[str] = "Unspecified",
        additional_info: Optional[str] = "",
        is_returning_patient: bool = False,
        patient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Tool 1: Validate patient inputs with comprehensive checks."""
        validation_errors = []

        # Validate Name
        cleaned_name = (patient_name or "").strip()
        if not cleaned_name or len(cleaned_name) < 2:
            validation_errors.append("Patient name or identifier must be at least 2 characters long.")

        # Validate Age
        if not isinstance(age, int) or age < 0 or age > 120:
            validation_errors.append("Patient age must be a valid integer between 0 and 120.")

        # Validate Described Concern
        cleaned_concern = (described_concern or "").strip()
        if not cleaned_concern or len(cleaned_concern) < 3:
            validation_errors.append("Described concern is too brief. Please describe symptoms clearly.")

        # Duration fallback
        cleaned_duration = (duration or "Unspecified").strip()

        is_valid = len(validation_errors) == 0

        return {
            "is_valid": is_valid,
            "errors": validation_errors,
            "cleaned_data": {
                "patient_name": cleaned_name,
                "age": age,
                "described_concern": cleaned_concern,
                "duration": cleaned_duration,
                "additional_info": (additional_info or "").strip(),
                "is_returning_patient": bool(is_returning_patient),
                "patient_id": (patient_id or "").strip() if patient_id else None
            }
        }

    @kernel_function(
        name="create_patient_record",
        description="Generates unique IDs, creates structured patient and session records, and persists them into the database."
    )
    def create_patient_record(
        self,
        cleaned_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Tool 2: Persist patient and intake session to SQLite database."""
        db = SessionLocal()
        try:
            # 1. Resolve or generate patient ID
            patient_id = cleaned_data.get("patient_id")
            if not patient_id:
                # Search if patient with exact name already exists
                existing_p = db.query(Patient).filter(Patient.full_name == cleaned_data["patient_name"]).first()
                if existing_p:
                    patient_id = existing_p.patient_id
                else:
                    patient_id = f"P-{uuid.uuid4().hex[:6].upper()}"
                    new_patient = Patient(
                        patient_id=patient_id,
                        full_name=cleaned_data["patient_name"],
                        age=cleaned_data["age"]
                    )
                    db.add(new_patient)
                    db.commit()

            # 2. Generate unique intake session ID
            session_id = f"INTK-{uuid.uuid4().hex[:8].upper()}"

            # 3. Create intake session record
            intake_session = IntakeSession(
                session_id=session_id,
                patient_id=patient_id,
                patient_name=cleaned_data["patient_name"],
                age=cleaned_data["age"],
                described_concern=cleaned_data["described_concern"],
                duration=cleaned_data["duration"],
                additional_info=cleaned_data.get("additional_info"),
                is_returning_patient=cleaned_data.get("is_returning_patient", False),
                status="PENDING",
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )
            db.add(intake_session)
            db.commit()

            return {
                "session_id": session_id,
                "patient_id": patient_id,
                "patient_name": cleaned_data["patient_name"],
                "age": cleaned_data["age"],
                "described_concern": cleaned_data["described_concern"],
                "duration": cleaned_data["duration"],
                "is_returning_patient": cleaned_data.get("is_returning_patient", False),
                "status": "RECORD_CREATED",
                "message": "Structured intake record created successfully."
            }
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"Database error creating patient record: {str(e)}")
        finally:
            db.close()


class IntakeAgent(BaseAgent):
    """
    Agent 1: Intake Agent.
    Responsible for validating incoming patient details and creating structured intake records.
    Never provides medical diagnosis.
    """

    def __init__(self):
        super().__init__(
            agent_name="Intake Agent",
            description="Collects and validates patient concerns and demographics into structured database records."
        )
        self.plugin = IntakePlugin(self)
        self.kernel.add_plugin(self.plugin, plugin_name="IntakePlugin")

    def run(self, raw_input: Dict[str, Any], execution_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Executes the Intake Agent workflow using Semantic Kernel plugin tools.
        """
        exec_id = execution_id or f"exec-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        self.create_execution_record(
            execution_id=exec_id,
            session_id=None,
            input_summary=f"Patient: {raw_input.get('patient_name')}, Age: {raw_input.get('age')}"
        )

        try:
            # Step 1: Tool 1 execution - validate_patient_input
            val_result = self.plugin.validate_patient_input(
                patient_name=raw_input.get("patient_name"),
                age=raw_input.get("age"),
                described_concern=raw_input.get("described_concern"),
                duration=raw_input.get("duration"),
                additional_info=raw_input.get("additional_info"),
                is_returning_patient=raw_input.get("is_returning_patient", False),
                patient_id=raw_input.get("patient_id")
            )

            self.log_tool_run(
                execution_id=exec_id,
                tool_name="validate_patient_input",
                input_args=raw_input,
                output_result=val_result,
                is_success=val_result["is_valid"],
                error_message="; ".join(val_result["errors"]) if not val_result["is_valid"] else None
            )

            if not val_result["is_valid"]:
                duration_ms = (time.time() - start_time) * 1000
                self.update_execution_record(
                    execution_id=exec_id,
                    status="FAILED",
                    output_summary="Input validation failed",
                    duration_ms=duration_ms,
                    error_details="; ".join(val_result["errors"])
                )
                return {
                    "success": False,
                    "execution_id": exec_id,
                    "errors": val_result["errors"],
                    "data": None
                }

            # Step 2: Tool 2 execution - create_patient_record
            record_result = self.plugin.create_patient_record(val_result["cleaned_data"])
            self.log_tool_run(
                execution_id=exec_id,
                tool_name="create_patient_record",
                input_args=val_result["cleaned_data"],
                output_result=record_result,
                is_success=True
            )

            duration_ms = (time.time() - start_time) * 1000
            self.update_execution_record(
                execution_id=exec_id,
                status="COMPLETED",
                output_summary=f"Created Session {record_result['session_id']} for Patient {record_result['patient_id']}",
                duration_ms=duration_ms
            )

            return {
                "success": True,
                "execution_id": exec_id,
                "tools_executed": ["validate_patient_input", "create_patient_record"],
                "data": record_result
            }

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.update_execution_record(
                execution_id=exec_id,
                status="FAILED",
                output_summary="Exception during intake processing",
                duration_ms=duration_ms,
                error_details=str(e)
            )
            self.log_tool_run(
                execution_id=exec_id,
                tool_name="create_patient_record",
                input_args=raw_input,
                output_result=None,
                is_success=False,
                error_message=str(e)
            )
            return {
                "success": False,
                "execution_id": exec_id,
                "errors": [str(e)],
                "data": None
            }
