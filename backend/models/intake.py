import datetime
from sqlalchemy import Column, String, Integer, Text, Boolean, DateTime, ForeignKey
from backend.database import Base

class IntakeSession(Base):
    __tablename__ = "intake_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(50), unique=True, index=True, nullable=False)
    patient_id = Column(String(50), nullable=False, index=True)
    patient_name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    described_concern = Column(Text, nullable=False)
    duration = Column(String(100), nullable=True)
    additional_info = Column(Text, nullable=True)
    is_returning_patient = Column(Boolean, default=False)
    status = Column(String(50), default="PENDING")  # PENDING, ROUTED, URGENT_STOP, COMPLETED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
