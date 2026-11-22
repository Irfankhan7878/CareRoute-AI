import re
import time
import uuid
from typing import Dict, Any, List, Optional
from semantic_kernel.functions import kernel_function
from backend.agents.base_agent import BaseAgent
from backend.config import settings

# Structured clinical warning patterns mapped to emergency categories
EMERGENCY_RULES = [
    {
        "category": "Cardiovascular Red Flags",
        "keywords": [
            r"\bchest pain\b", r"\bcrushing chest\b", r"\bchest pressure\b",
            r"\bpain radiating to (?:arm|jaw|neck|back)\b", r"\bheart attack\b",
            r"\bcardiac arrest\b", r"\bsudden irregular racing heart with fainting\b"
        ],
        "description": "Acute chest discomfort or pain indicative of potential acute coronary syndrome or myocardial infarction."
    },
    {
        "category": "Respiratory Red Flags",
        "keywords": [
            r"\bdifficulty breathing\b", r"\bshortness of breath\b", r"\bcannot breathe\b",
            r"\bcan't breathe\b", r"\bgasping\b", r"\bchoking\b", r"\bstridor\b",
            r"\bturning blue\b", r"\bcyanosis\b", r"\bsevere asthma attack\b"
        ],
        "description": "Acute respiratory compromise or impending airway obstruction."
    },
    {
        "category": "Neurological / Stroke Red Flags",
        "keywords": [
            r"\bslurred speech\b", r"\bfacial droop\b", r"\bone-sided numbness\b",
            r"\bweakness in (?:arm|leg|one side)\b", r"\bsudden blindness\b",
            r"\bthunderclap headache\b", r"\bworst headache of (?:my|his|her) life\b",
            r"\bloss of consciousness\b", r"\bpassed out and won't wake up\b",
            r"\bunresponsive\b", r"\bseizure\b", r"\bconvulsing\b"
        ],
        "description": "Acute neurological deficits, altered mental status, or potential cerebrovascular accident (FAST signs)."
    },
    {
        "category": "Severe Hemorrhage / Acute Trauma",
        "keywords": [
            r"\buncontrolled bleeding\b", r"\bgushing blood\b", r"\bcoughing up (?:large amounts of )?blood\b",
            r"\bvomi(?:t|ting) blood\b", r"\bsevere trauma\b", r"\bdeep stab wound\b",
            r"\bgunshot\b", r"\bhead injury with loss of consciousness\b"
        ],
        "description": "Active major hemorrhage or high-velocity acute physical trauma."
    },
    {
        "category": "Anaphylaxis / Severe Allergy",
        "keywords": [
            r"\bthroat (?:closing|swelling)\b", r"\btongue swelling\b", r"\blips swelling with rash\b",
            r"\banaphylaxis\b", r"\bepipen\b"
        ],
        "description": "Severe systemic allergic reaction compromising upper airway or hemodynamics."
    }
]

class SafetyGatePlugin:
    """
    Microsoft Semantic Kernel Plugin for Safety Gate Agent.
    Contains real Python tools for urgent warning signs detection and emergency advisory generation.
    """

    def __init__(self, agent: "SafetyGateAgent"):
        self.agent = agent

    @kernel_function(
        name="detect_urgent_warning_signs",
        description="Scans patient symptoms and history against clinical emergency red-flag warning rules."
    )
    def detect_urgent_warning_signs(
        self,
        described_concern: str,
        age: Optional[int] = None,
        additional_info: Optional[str] = ""
    ) -> Dict[str, Any]:
        """Tool 1: Evaluate concern against urgent emergency rules."""
        full_text = f"{described_concern or ''} {additional_info or ''}".lower()
        matched_indicators = []
        matched_categories = []

        for rule in EMERGENCY_RULES:
            for pattern in rule["keywords"]:
                if re.search(pattern, full_text):
                    indicator = f"{rule['category']}: matched expression '{pattern.replace(r'\b', '').replace('(?:', '').replace(')', '')}'"
                    matched_indicators.append(indicator)
                    if rule["category"] not in matched_categories:
                        matched_categories.append(rule["category"])

        is_urgent = len(matched_indicators) > 0

        return {
            "is_urgent": is_urgent,
            "warning_signs_detected": matched_indicators,
            "affected_categories": matched_categories,
            "checked_text_length": len(full_text)
        }

    @kernel_function(
        name="generate_urgent_care_advisory",
        description="Generates an immediate emergency advisory instructing the patient to seek acute in-person care."
    )
    def generate_urgent_care_advisory(
        self,
        warning_signs: List[str],
        patient_name: Optional[str] = "Patient"
    ) -> Dict[str, Any]:
        """Tool 2: Formulate emergency action advisory and hotline information."""
        advisory_text = (
            f"EMERGENCY WARNING: Potential high-risk medical indicators were detected in the description:\n"
            + "\n".join([f"- {w}" for w in warning_signs])
            + "\n\n"
            "IMMEDIATE ACTION REQUIRED:\n"
            "1. Normal hospital department routing has been HALTED for patient safety.\n"
            "2. Routine outpatient appointment booking is NOT appropriate for acute emergency symptoms.\n"
            "3. Please proceed immediately to the nearest Hospital Emergency Department (Ground Floor, Red Wing) "
            "or contact local emergency services immediately (Dial 911 / 112 / 108 / 999).\n"
            "4. Do not attempt to drive yourself if you are feeling dizzy, short of breath, or experiencing chest discomfort.\n\n"
            + settings.MANDATORY_DISCLAIMER
        )

        return {
            "urgency_level": "CRITICAL_EMERGENCY",
            "advisory_message": advisory_text,
            "emergency_numbers": ["112 (Universal Emergency)", "911 / 999 (National Dispatch)", "108 (Ambulance Hotline)"],
            "recommended_department": "Emergency Department (Walk-in Immediate)",
            "normal_routing_halted": True
        }


class SafetyGateAgent(BaseAgent):
    """
    Agent 5: Safety Gate Agent.
    Mandatory gatekeeper evaluating incoming concerns for urgent clinical warning signs.
    Stops normal routing when red flags are identified and issues emergency care advisories.
    Never allows another agent to override a safety stop.
    """

    def __init__(self):
        super().__init__(
            agent_name="Safety Gate Agent",
            description="Evaluates symptoms for life-threatening or urgent warning signs and halts non-emergent routing."
        )
        self.plugin = SafetyGatePlugin(self)
        self.kernel.add_plugin(self.plugin, plugin_name="SafetyGatePlugin")

    def run(
        self,
        described_concern: str,
        patient_name: str = "Patient",
        age: Optional[int] = None,
        additional_info: Optional[str] = "",
        execution_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes safety evaluation workflow.
        """
        exec_id = execution_id or f"exec-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        self.create_execution_record(
            execution_id=exec_id,
            session_id=session_id,
            input_summary=f"Checking concern: '{described_concern[:60]}...' (Age: {age})"
        )

        try:
            # Step 1: Tool 1 execution - detect_urgent_warning_signs
            detection_result = self.plugin.detect_urgent_warning_signs(
                described_concern=described_concern,
                age=age,
                additional_info=additional_info
            )

            self.log_tool_run(
                execution_id=exec_id,
                tool_name="detect_urgent_warning_signs",
                input_args={"described_concern": described_concern, "age": age},
                output_result=detection_result,
                is_success=True
            )

            is_urgent = detection_result["is_urgent"]
            advisory_data = None
            tools_called = ["detect_urgent_warning_signs"]

            # Step 2: Tool 2 execution - generate_urgent_care_advisory (if urgent)
            if is_urgent:
                advisory_data = self.plugin.generate_urgent_care_advisory(
                    warning_signs=detection_result["warning_signs_detected"],
                    patient_name=patient_name
                )
                tools_called.append("generate_urgent_care_advisory")

                self.log_tool_run(
                    execution_id=exec_id,
                    tool_name="generate_urgent_care_advisory",
                    input_args={"warning_signs": detection_result["warning_signs_detected"]},
                    output_result=advisory_data,
                    is_success=True
                )

            duration_ms = (time.time() - start_time) * 1000
            status = "STOPPED_FOR_SAFETY" if is_urgent else "COMPLETED"
            summary = (
                f"SAFETY STOP TRIGGERED: {len(detection_result['warning_signs_detected'])} red flag(s) identified."
                if is_urgent
                else "Safety check passed: No acute emergency signs detected."
            )

            self.update_execution_record(
                execution_id=exec_id,
                status=status,
                output_summary=summary,
                duration_ms=duration_ms
            )

            return {
                "success": True,
                "execution_id": exec_id,
                "is_urgent": is_urgent,
                "safety_status": "URGENT_STOP" if is_urgent else "NORMAL",
                "warning_signs": detection_result["warning_signs_detected"],
                "categories": detection_result["affected_categories"],
                "advisory": advisory_data["advisory_message"] if advisory_data else None,
                "tools_executed": tools_called,
                "disclaimer": settings.MANDATORY_DISCLAIMER
            }

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.update_execution_record(
                execution_id=exec_id,
                status="FAILED",
                output_summary="Safety Gate check error",
                duration_ms=duration_ms,
                error_details=str(e)
            )
            # Fail-safe: if safety gate errors out, assume precautionary safety stop!
            return {
                "success": False,
                "execution_id": exec_id,
                "is_urgent": True,
                "safety_status": "URGENT_STOP",
                "warning_signs": ["System safety check error; defaulting to precautionary emergency evaluation"],
                "advisory": "A safety processing error occurred. For patient protection, please proceed to an emergency clinic or consult a physician immediately.",
                "tools_executed": ["detect_urgent_warning_signs"],
                "disclaimer": settings.MANDATORY_DISCLAIMER
            }
