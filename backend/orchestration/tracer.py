import datetime
from typing import List, Dict, Any, Optional

class OrchestrationTracer:
    """
    Tracks and records the multi-agent execution lifecycle in real-time.
    Captures exact timestamps, durations, tool calls, and state transitions.
    """

    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id
        self.traces: List[Dict[str, Any]] = []

    def start_agent_step(self, agent_name: str, execution_id: str, input_summary: Optional[str] = None) -> Dict[str, Any]:
        """Initializes a running trace record for an agent."""
        step = {
            "agent_name": agent_name,
            "execution_id": execution_id,
            "status": "Running",
            "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "completed_at": None,
            "duration_ms": None,
            "tools_executed": [],
            "input_summary": input_summary,
            "output_summary": None,
            "error_details": None
        }
        self.traces.append(step)
        return step

    def complete_agent_step(
        self,
        agent_name: str,
        execution_id: str,
        status: str,
        tools_executed: List[str],
        output_summary: Optional[str] = None,
        duration_ms: Optional[float] = None,
        error_details: Optional[str] = None
    ):
        """Finalizes trace record for an agent."""
        for step in reversed(self.traces):
            if step["agent_name"] == agent_name and step["execution_id"] == execution_id:
                step["status"] = status
                step["completed_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
                step["tools_executed"] = tools_executed
                step["output_summary"] = output_summary
                step["duration_ms"] = round(duration_ms, 2) if duration_ms is not None else None
                step["error_details"] = error_details
                break

    def get_traces(self) -> List[Dict[str, Any]]:
        """Returns the full list of captured agent execution traces."""
        return self.traces
