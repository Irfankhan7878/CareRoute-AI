import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from backend.database import Base

class RoutingRecord(Base):
    __tablename__ = "routing_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(50), nullable=False, index=True)
    patient_id = Column(String(50), nullable=False, index=True)
    selected_department = Column(String(100), nullable=False)
    department_code = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    alternative_department = Column(String(100), nullable=True)
    safety_status = Column(String(50), default="NORMAL")  # NORMAL, URGENT_STOP
    advisory_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
