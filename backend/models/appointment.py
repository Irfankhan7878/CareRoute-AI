import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint
from backend.database import Base

class AppointmentSlot(Base):
    __tablename__ = "appointment_slots"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    department_code = Column(String(50), nullable=False, index=True)
    date = Column(String(20), nullable=False, index=True)  # YYYY-MM-DD
    time_slot = Column(String(20), nullable=False)         # HH:MM AM/PM
    doctor_name = Column(String(100), nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint('department_code', 'date', 'time_slot', 'doctor_name', name='uq_department_date_time_doctor'),
    )

class AppointmentBooking(Base):
    __tablename__ = "appointment_bookings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    booking_reference = Column(String(50), unique=True, index=True, nullable=False)
    slot_id = Column(Integer, ForeignKey("appointment_slots.id"), unique=True, nullable=False)
    patient_id = Column(String(50), nullable=False, index=True)
    patient_name = Column(String(100), nullable=False)
    department_code = Column(String(50), nullable=False)
    department_name = Column(String(100), nullable=False)
    appointment_date = Column(String(20), nullable=False)
    time_slot = Column(String(20), nullable=False)
    doctor_name = Column(String(100), nullable=False)
    status = Column(String(50), default="CONFIRMED")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
