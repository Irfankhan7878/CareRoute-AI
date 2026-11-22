import time
import uuid
import datetime
from typing import Dict, Any, List, Optional
from semantic_kernel.functions import kernel_function
from backend.agents.base_agent import BaseAgent
from backend.database import SessionLocal
from backend.models.appointment import AppointmentSlot, AppointmentBooking
from backend.models.department import Department
from backend.config import settings

class AppointmentPlugin:
    """
    Microsoft Semantic Kernel Plugin for Appointment Agent.
    Contains real Python tools for retrieving available slots and reserving appointment bookings.
    """

    def __init__(self, agent: "AppointmentAgent"):
        self.agent = agent

    @kernel_function(
        name="get_available_appointment_slots",
        description="Queries database for available demonstration appointment slots filtered by hospital department code and optional target date."
    )
    def get_available_appointment_slots(
        self,
        department_code: str,
        target_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Tool 1: Read available slots from SQLite database."""
        db = SessionLocal()
        try:
            query = db.query(AppointmentSlot).filter(
                AppointmentSlot.department_code == department_code,
                AppointmentSlot.is_available == True
            )

            if target_date:
                query = query.filter(AppointmentSlot.date == target_date)

            slots = query.order_by(AppointmentSlot.date.asc(), AppointmentSlot.time_slot.asc()).limit(15).all()

            slot_list = [
                {
                    "slot_id": s.id,
                    "department_code": s.department_code,
                    "date": s.date,
                    "time_slot": s.time_slot,
                    "doctor_name": s.doctor_name,
                    "is_available": s.is_available
                }
                for s in slots
            ]

            return {
                "department_code": department_code,
                "total_available": len(slot_list),
                "slots": slot_list,
                "has_slots": len(slot_list) > 0,
                "notice": "DEMONSTRATION BOOKINGS ONLY: These slots are synthetic demonstration records, not real hospital slots."
            }
        finally:
            db.close()

    @kernel_function(
        name="reserve_appointment_slot",
        description="Reserves an appointment slot atomically, updating availability, preventing double-bookings, and generating a reference ID."
    )
    def reserve_appointment_slot(
        self,
        slot_id: int,
        patient_id: str,
        patient_name: str
    ) -> Dict[str, Any]:
        """Tool 2: Atomically reserve a slot and create confirmed booking record."""
        db = SessionLocal()
        try:
            # Check slot existence and availability
            slot = db.query(AppointmentSlot).filter(AppointmentSlot.id == slot_id).first()
            if not slot:
                return {
                    "success": False,
                    "booking_reference": None,
                    "message": f"Appointment slot ID {slot_id} does not exist."
                }

            if not slot.is_available:
                return {
                    "success": False,
                    "booking_reference": None,
                    "message": f"Appointment slot ID {slot_id} has already been reserved by another patient. Duplicate booking prevented."
                }

            # Check if patient already booked this exact slot
            existing_booking = db.query(AppointmentBooking).filter(
                AppointmentBooking.slot_id == slot_id
            ).first()
            if existing_booking:
                return {
                    "success": False,
                    "booking_reference": None,
                    "message": "This slot already has an active confirmed booking."
                }

            # Retrieve department name
            dept = db.query(Department).filter(Department.code == slot.department_code).first()
            dept_name = dept.name if dept else slot.department_code

            # Generate unique booking reference ID
            booking_ref = f"BK-{uuid.uuid4().hex[:6].upper()}"

            # Mark slot unavailable
            slot.is_available = False

            # Create booking record
            new_booking = AppointmentBooking(
                booking_reference=booking_ref,
                slot_id=slot.id,
                patient_id=patient_id,
                patient_name=patient_name,
                department_code=slot.department_code,
                department_name=dept_name,
                appointment_date=slot.date,
                time_slot=slot.time_slot,
                doctor_name=slot.doctor_name,
                status="CONFIRMED",
                created_at=datetime.datetime.now(datetime.timezone.utc)
            )
            db.add(new_booking)
            db.commit()

            return {
                "success": True,
                "booking_reference": booking_ref,
                "slot_id": slot.id,
                "patient_id": patient_id,
                "patient_name": patient_name,
                "department_code": slot.department_code,
                "department_name": dept_name,
                "appointment_date": slot.date,
                "time_slot": slot.time_slot,
                "doctor_name": slot.doctor_name,
                "status": "CONFIRMED",
                "message": f"Demonstration appointment reserved successfully with reference {booking_ref}.",
                "disclaimer": "DEMONSTRATION BOOKING: This reservation is simulated for system testing and does not represent a real clinical appointment."
            }
        except Exception as e:
            db.rollback()
            return {
                "success": False,
                "booking_reference": None,
                "message": f"Booking failed due to database conflict: {str(e)}"
            }
        finally:
            db.close()


class AppointmentAgent(BaseAgent):
    """
    Agent 4: Appointment Agent.
    Retrieves and reserves demonstration appointment slots from the database.
    Prevents duplicate bookings and clearly identifies appointments as simulated demo bookings.
    """

    def __init__(self):
        super().__init__(
            agent_name="Appointment Agent",
            description="Manages demonstration appointment availability and reservations for hospital departments."
        )
        self.plugin = AppointmentPlugin(self)
        self.kernel.add_plugin(self.plugin, plugin_name="AppointmentPlugin")

    def run(
        self,
        department_code: str,
        target_date: Optional[str] = None,
        execution_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes appointment retrieval workflow.
        """
        exec_id = execution_id or f"exec-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        self.create_execution_record(
            execution_id=exec_id,
            session_id=session_id,
            input_summary=f"Querying slots for dept: {department_code}, date: {target_date}"
        )

        try:
            # Step 1: Tool 1 execution - get_available_appointment_slots
            slots_data = self.plugin.get_available_appointment_slots(
                department_code=department_code,
                target_date=target_date
            )
            self.log_tool_run(
                execution_id=exec_id,
                tool_name="get_available_appointment_slots",
                input_args={"department_code": department_code, "target_date": target_date},
                output_result=slots_data,
                is_success=True
            )

            duration_ms = (time.time() - start_time) * 1000
            summary = f"Found {slots_data['total_available']} slots for {department_code}"
            self.update_execution_record(
                execution_id=exec_id,
                status="COMPLETED",
                output_summary=summary,
                duration_ms=duration_ms
            )

            return {
                "success": True,
                "execution_id": exec_id,
                "tools_executed": ["get_available_appointment_slots"],
                "data": slots_data
            }

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.update_execution_record(
                execution_id=exec_id,
                status="FAILED",
                output_summary="Failed retrieving appointment slots",
                duration_ms=duration_ms,
                error_details=str(e)
            )
            return {
                "success": False,
                "execution_id": exec_id,
                "errors": [str(e)],
                "data": {
                    "department_code": department_code,
                    "total_available": 0,
                    "slots": [],
                    "has_slots": False,
                    "notice": "Unable to load appointment slots at this time."
                }
            }

    def book(
        self,
        slot_id: int,
        patient_id: str,
        patient_name: str,
        execution_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Direct booking execution through reserve_appointment_slot tool."""
        exec_id = execution_id or f"exec-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        self.create_execution_record(
            execution_id=exec_id,
            session_id=None,
            input_summary=f"Booking slot {slot_id} for {patient_name} ({patient_id})"
        )

        res = self.plugin.reserve_appointment_slot(
            slot_id=slot_id,
            patient_id=patient_id,
            patient_name=patient_name
        )

        self.log_tool_run(
            execution_id=exec_id,
            tool_name="reserve_appointment_slot",
            input_args={"slot_id": slot_id, "patient_id": patient_id, "patient_name": patient_name},
            output_result=res,
            is_success=res["success"],
            error_message=res.get("message") if not res["success"] else None
        )

        duration_ms = (time.time() - start_time) * 1000
        status = "COMPLETED" if res["success"] else "FAILED"
        self.update_execution_record(
            execution_id=exec_id,
            status=status,
            output_summary=res.get("message"),
            duration_ms=duration_ms
        )

        return res
