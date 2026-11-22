import json
import uuid
import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from semantic_kernel import Kernel
from backend.config import settings
from backend.database import SessionLocal
from backend.models.execution_log import AgentExecution, AgentToolLog

class BaseAgent:
    """
    Abstract Base Agent integrating with Microsoft Semantic Kernel.
    Provides execution tracing, tool registration, append-only logging, and error handling.
    """

    def __init__(self, agent_name: str, description: str):
        self.agent_name = agent_name
        self.description = description
        self.kernel = Kernel()
        self.log_path = Path(settings.EXECUTION_LOG_PATH)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_tool_run(
        self,
        execution_id: str,
        tool_name: str,
        input_args: Dict[str, Any],
        output_result: Any,
        is_success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Appends tool execution entry to logs/agent_runs.jsonl and persists to database.
        """
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # 1. Append to JSONL log
        log_entry = {
            "execution_id": execution_id,
            "agent_name": self.agent_name,
            "timestamp": now_iso,
            "tool_name": tool_name,
            "input_args": input_args,
            "execution_result": output_result,
            "is_success": is_success,
            "error_details": error_message
        }
        
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, default=str) + "\n")
        except Exception as e:
            print(f"[LOGGING ERROR] Failed writing to {self.log_path}: {e}")

        # 2. Persist to DB AgentToolLog
        try:
            db = SessionLocal()
            tool_record = AgentToolLog(
                execution_id=execution_id,
                agent_name=self.agent_name,
                tool_name=tool_name,
                input_args=json.dumps(input_args, default=str),
                output_result=json.dumps(output_result, default=str) if output_result is not None else None,
                timestamp=datetime.datetime.now(datetime.timezone.utc),
                is_success=is_success,
                error_message=error_message
            )
            db.add(tool_record)
            db.commit()
            db.close()
        except Exception as db_err:
            print(f"[DB LOGGING ERROR] Failed saving tool log: {db_err}")

    def create_execution_record(self, execution_id: str, session_id: Optional[str], input_summary: str):
        """Creates an initial agent execution record in database."""
        try:
            db = SessionLocal()
            record = AgentExecution(
                execution_id=execution_id,
                session_id=session_id,
                agent_name=self.agent_name,
                status="RUNNING",
                started_at=datetime.datetime.now(datetime.timezone.utc),
                input_summary=input_summary
            )
            db.add(record)
            db.commit()
            db.close()
        except Exception as e:
            print(f"[DB ERROR] Failed creating execution record: {e}")

    def update_execution_record(
        self,
        execution_id: str,
        status: str,
        output_summary: Optional[str] = None,
        duration_ms: Optional[float] = None,
        error_details: Optional[str] = None
    ):
        """Updates agent execution record upon completion or failure."""
        try:
            db = SessionLocal()
            record = db.query(AgentExecution).filter(AgentExecution.execution_id == execution_id).first()
            if record:
                record.status = status
                record.completed_at = datetime.datetime.now(datetime.timezone.utc)
                record.output_summary = output_summary
                record.duration_ms = duration_ms
                record.error_details = error_details
                db.commit()
            db.close()
        except Exception as e:
            print(f"[DB ERROR] Failed updating execution record: {e}")
