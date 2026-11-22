from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import datetime

class AgentExecutionSummary(BaseModel):
    execution_id: str
    session_id: Optional[str]
    agent_name: str
    status: str
    started_at: datetime.datetime
    duration_ms: Optional[float]
    input_summary: Optional[str]
    output_summary: Optional[str]
    error_details: Optional[str]

class AdminDashboardResponse(BaseModel):
    total_intake_sessions: int
    completed_routings: int
    urgent_safety_stops: int
    total_appointments_booked: int
    recent_executions: List[AgentExecutionSummary]
    recent_tool_logs: List[Dict[str, Any]]
    rag_retrieval_activity: List[Dict[str, Any]]
