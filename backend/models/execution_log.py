import datetime
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, DateTime
from backend.database import Base

class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    execution_id = Column(String(50), unique=True, index=True, nullable=False)
    session_id = Column(String(50), nullable=True, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False)  # PENDING, RUNNING, COMPLETED, FAILED, STOPPED_FOR_SAFETY
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Float, nullable=True)
    input_summary = Column(Text, nullable=True)
    output_summary = Column(Text, nullable=True)
    error_details = Column(Text, nullable=True)

class AgentToolLog(Base):
    __tablename__ = "agent_tool_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    execution_id = Column(String(50), nullable=False, index=True)
    agent_name = Column(String(100), nullable=False, index=True)
    tool_name = Column(String(100), nullable=False, index=True)
    input_args = Column(Text, nullable=True)
    output_result = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    is_success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
