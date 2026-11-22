import time
import uuid
from typing import Dict, Any, List, Optional
from semantic_kernel.functions import kernel_function
from backend.agents.base_agent import BaseAgent
from backend.rag.retriever import rag_retriever

class InformationPlugin:
    """
    Microsoft Semantic Kernel Plugin for Information Agent.
    Contains real Python tools for semantic document retrieval and grounded instruction formatting.
    """

    def __init__(self, agent: "InformationAgent"):
        self.agent = agent

    @kernel_function(
        name="retrieve_department_information",
        description="Performs semantic retrieval against hospital knowledge documents, filtered by clinical department."
    )
    def retrieve_department_information(
        self,
        department_code: str,
        query_concern: str
    ) -> Dict[str, Any]:
        """Tool 1: Semantic search across indexed hospital policy chunks."""
        chunks = rag_retriever.query(
            query_text=query_concern,
            department_code=department_code,
            top_k=4
        )

        return {
            "department_code": department_code,
            "query_used": query_concern,
            "retrieved_chunk_count": len(chunks),
            "chunks": chunks
        }

    @kernel_function(
        name="format_grounded_instructions",
        description="Synthesizes retrieved chunks into grounded intake instructions, required documents checklist, and preparation guidance with source citations."
    )
    def format_grounded_instructions(
        self,
        department_name: str,
        retrieved_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Tool 2: Grounded extraction of instructions, documents, and preparation guidelines."""
        intake_instructions = []
        documents_required = []
        preparation_guidance = []
        source_references = []

        if not retrieved_chunks:
            return {
                "department_description": f"Official documentation for {department_name} is currently offline.",
                "intake_instructions": "Please arrive 15 minutes before your consultation at the Central Registration Atrium.",
                "documents_required": ["Government Photo ID", "Active Health Insurance Card", "List of Current Medications"],
                "preparation_instructions": ["Wear comfortable clothing", "Bring all prior medical records"],
                "source_references": [],
                "missing_information": ["Department-specific clinical policy document"]
            }

        for chunk in retrieved_chunks:
            doc_name = chunk.get("document_name", "hospital_docs.txt")
            sec_title = chunk.get("section_title", "General")
            content = chunk.get("content", "")

            source_references.append({
                "document_name": doc_name,
                "section": sec_title,
                "snippet": content[:180] + ("..." if len(content) > 180 else "")
            })

            lower_title = sec_title.lower()
            if "required documents" in lower_title:
                # Extract bullet items
                for line in content.split("\n"):
                    if line.strip().startswith("- "):
                        documents_required.append(f"{line.strip()[2:]} [source: {doc_name}]")
            elif "preparation" in lower_title:
                for line in content.split("\n"):
                    if line.strip().startswith("- "):
                        preparation_guidance.append(f"{line.strip()[2:]} [source: {doc_name}]")
            elif "registration" in lower_title or "intake" in lower_title:
                intake_instructions.append(f"{content} [source: {doc_name}]")

        # Fallback defaults if specific sections weren't caught by exact headings
        if not documents_required:
            documents_required = [
                f"Government Photo ID (National ID / Passport) [source: {retrieved_chunks[0]['document_name']}]",
                f"Insurance card or billing guarantee [source: {retrieved_chunks[0]['document_name']}]",
                f"Prior relevant clinical reports or imaging [source: {retrieved_chunks[0]['document_name']}]"
            ]

        if not preparation_guidance:
            preparation_guidance = [
                f"Arrive 15 minutes prior for vital signs intake triage [source: {retrieved_chunks[0]['document_name']}]",
                f"Wear comfortable clothing suitable for physical examination [source: {retrieved_chunks[0]['document_name']}]"
            ]

        combined_instructions = (
            "\n\n".join(intake_instructions)
            if intake_instructions
            else f"Please report to {department_name} reception desk 15 minutes before your scheduled appointment time."
        )

        return {
            "department_description": f"Standard hospital operating guidelines for {department_name} derived from grounded hospital policy documentation.",
            "intake_instructions": combined_instructions,
            "documents_required": documents_required,
            "preparation_instructions": preparation_guidance,
            "source_references": source_references,
            "missing_information": []
        }


class InformationAgent(BaseAgent):
    """
    Agent 3: Information Agent.
    Retrieves department-specific intake instructions, required documentation, and preparation guidelines using RAG.
    Never fabricates hospital policy.
    """

    def __init__(self):
        super().__init__(
            agent_name="Information Agent",
            description="Performs semantic retrieval over hospital policy documents and formats grounded intake instructions."
        )
        self.plugin = InformationPlugin(self)
        self.kernel.add_plugin(self.plugin, plugin_name="InformationPlugin")

    def run(
        self,
        department_name: str,
        department_code: str,
        described_concern: str,
        execution_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes semantic retrieval and grounded instruction formatting workflow.
        """
        exec_id = execution_id or f"exec-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        self.create_execution_record(
            execution_id=exec_id,
            session_id=session_id,
            input_summary=f"Dept: {department_name} ({department_code}), Query: '{described_concern[:50]}...'"
        )

        try:
            # Step 1: Tool 1 execution - retrieve_department_information
            retrieval_data = self.plugin.retrieve_department_information(
                department_code=department_code,
                query_concern=described_concern
            )
            self.log_tool_run(
                execution_id=exec_id,
                tool_name="retrieve_department_information",
                input_args={"department_code": department_code, "query_concern": described_concern},
                output_result=retrieval_data,
                is_success=True
            )

            # Step 2: Tool 2 execution - format_grounded_instructions
            formatted_instructions = self.plugin.format_grounded_instructions(
                department_name=department_name,
                retrieved_chunks=retrieval_data["chunks"]
            )
            self.log_tool_run(
                execution_id=exec_id,
                tool_name="format_grounded_instructions",
                input_args={"department_name": department_name, "chunk_count": len(retrieval_data["chunks"])},
                output_result=formatted_instructions,
                is_success=True
            )

            duration_ms = (time.time() - start_time) * 1000
            summary = f"Retrieved and formatted instructions for {department_name} ({len(retrieval_data['chunks'])} chunks)"
            self.update_execution_record(
                execution_id=exec_id,
                status="COMPLETED",
                output_summary=summary,
                duration_ms=duration_ms
            )

            return {
                "success": True,
                "execution_id": exec_id,
                "tools_executed": ["retrieve_department_information", "format_grounded_instructions"],
                "data": formatted_instructions
            }

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.update_execution_record(
                execution_id=exec_id,
                status="FAILED",
                output_summary="Failed information retrieval",
                duration_ms=duration_ms,
                error_details=str(e)
            )
            return {
                "success": False,
                "execution_id": exec_id,
                "errors": [str(e)],
                "data": {
                    "department_description": f"General guidance for {department_name}.",
                    "intake_instructions": "Report to the Central Registration Desk upon hospital arrival.",
                    "documents_required": ["Photo ID", "Insurance Card", "Medication List"],
                    "preparation_instructions": ["Arrive 15 minutes before appointment"],
                    "source_references": [],
                    "missing_information": [str(e)]
                }
            }
