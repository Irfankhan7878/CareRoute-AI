from pydantic import BaseModel, Field
from typing import Optional
import datetime

class AppointmentSlotResponse(BaseModel):
    id: int
    department_code: str
    date: str
    time_slot: str
    doctor_name: str
    is_available: bool

class BookAppointmentRequest(BaseModel):
    slot_id: int = Field(..., description="ID of the appointment slot to reserve")
    patient_id: str = Field(..., min_length=1, description="Patient ID")
    patient_name: str = Field(..., min_length=2, description="Patient Name")

class BookAppointmentResponse(BaseModel):
    booking_reference: str
    slot_id: int
    patient_id: str
    patient_name: str
    department_code: str
    department_name: str
    appointment_date: str
    time_slot: str
    doctor_name: str
    status: str
    message: str
    disclaimer: str
