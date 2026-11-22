import re
import time
import uuid
from typing import Dict, Any, Optional, Tuple, List
from semantic_kernel.functions import kernel_function
from backend.agents.base_agent import BaseAgent
from backend.database import SessionLocal
from backend.models.department import Department

# Clinical routing keyword rules for each hospital department
DEPARTMENT_ROUTING_RULES = [
    {
        "code": "PAED",
        "name": "Paediatrics",
        "keywords": [
            r"\bchild\b", r"\binfant\b", r"\bbaby\b", r"\btoddler\b", r"\bpediatric\b",
            r"\bpaediatric\b", r"\bson\b", r"\bdaughter\b", r"\bkid\b"
        ],
        "age_max": 17,
        "priority": 10,
        "base_reason": "Patient is within paediatric age range (<18 years) or concerns paediatric care."
    },
    {
        "code": "ORTHO",
        "name": "Orthopaedics",
        "keywords": [
            r"\bknee\b", r"\bjoint\b", r"\bbone\b", r"\bfracture\b", r"\bsprain\b",
            r"\bligament\b", r"\bswollen ankle\b", r"\bshoulder pain\b", r"\bhip pain\b",
            r"\bback pain\b", r"\bspine\b", r"\bcartilage\b", r"\barthritis\b", r"\btendon\b",
            r"\bwalking difficulty\b", r"\blimping\b", r"\borthopedic\b"
        ],
        "priority": 5,
        "base_reason": "Musculoskeletal symptoms involving joints, bones, or soft tissue injury."
    },
    {
        "code": "ENT",
        "name": "ENT (Ear, Nose & Throat)",
        "keywords": [
            r"\bear\b", r"\bearache\b", r"\bhearing\b", r"\btinnitus\b", r"\bthroat\b",
            r"\bsore throat\b", r"\btonsil\b", r"\bnose\b", r"\bnosebleed\b", r"\bsinus\b",
            r"\bsinusitis\b", r"\bhoarseness\b", r"\bvocal cord\b", r"\bcongestion\b",
            r"\bswallowing pain\b", r"\bclogged ears\b"
        ],
        "priority": 5,
        "base_reason": "Upper respiratory and otolaryngological symptoms affecting ears, nose, or throat."
    },
    {
        "code": "CARDIO",
        "name": "Cardiology",
        "keywords": [
            r"\bpalpitation\b", r"\bracing heart\b", r"\bheart fluttering\b", r"\bhigh blood pressure\b",
            r"\bhypertension\b", r"\bcardiac checkup\b", r"\becg\b", r"\bcholesterol check\b",
            r"\birregular pulse\b", r"\bheart murmur\b"
        ],
        "priority": 6,
        "base_reason": "Cardiovascular signs, pulse irregularities, or routine heart health concerns."
    },
    {
        "code": "DERM",
        "name": "Dermatology",
        "keywords": [
            r"\bskin\b", r"\brash\b", r"\beczema\b", r"\bpsoriasis\b", r"\bitching\b",
            r"\bhives\b", r"\bacne\b", r"\bmole\b", r"\bdermatitis\b", r"\bskin lesion\b",
            r"\bdandruff\b", r"\bhair loss\b", r"\bnail infection\b", r"\bblister\b"
        ],
        "priority": 5,
        "base_reason": "Dermatological manifestations involving cutaneous surfaces, rashes, or lesions."
    },
    {
        "code": "GASTRO",
        "name": "Gastroenterology",
        "keywords": [
            r"\bstomach\b", r"\babdomen\b", r"\babdominal pain\b", r"\bgastric\b", r"\bacidity\b",
            r"\bheartburn\b", r"\breflux\b", r"\bgerd\b", r"\bindigestion\b", r"\bnausea\b",
            r"\bvomiting\b", r"\bdiarrhea\b", r"\bconstipation\b", r"\bbloating\b", r"\bbowel\b",
            r"\bgallbladder\b", r"\bliver\b"
        ],
        "priority": 5,
        "base_reason": "Gastrointestinal and digestive symptoms involving abdominal discomfort or bowel changes."
    },
    {
        "code": "NEURO",
        "name": "Neurology",
        "keywords": [
            r"\bheadache\b", r"\bmigraine\b", r"\btremor\b", r"\bshaking hands\b",
            r"\bnumbness\b", r"\btingling\b", r"\bneuropathy\b", r"\bpin and needles\b",
            r"\bdizziness\b", r"\bvertigo\b", r"\bmemory lapse\b", r"\bforgetfulness\b"
        ],
        "priority": 5,
        "base_reason": "Neurological presentations including persistent headaches, paresthesias, or dizziness."
    },
    {
        "code": "OPHTH",
        "name": "Ophthalmology",
        "keywords": [
            r"\beye\b", r"\bvision\b", r"\bblurry vision\b", r"\bdouble vision\b", r"\beye strain\b",
            r"\bred eye\b", r"\bconjunctivitis\b", r"\bitchy eyes\b", r"\beye pain\b",
            r"\bfloaters\b", r"\bcontact lens irritation\b", r"\bglaucoma\b", r"\bcataract\b"
        ],
        "priority": 5,
        "base_reason": "Ophthalmic symptoms regarding ocular health, vision disturbances, or eye discomfort."
    },
    {
        "code": "GYNAE",
        "name": "Gynaecology",
        "keywords": [
            r"\bperiod\b", r"\bmenstrua(?:l|tion)\b", r"\bpregnancy\b", r"\bpregnant\b",
            r"\bpelvic pain\b", r"\bvaginal\b", r"\bmenopause\b", r"\bhot flash\b",
            r"\bovary\b", r"\buterus\b", r"\bpap smear\b", r"\bpcos\b"
        ],
        "priority": 6,
        "base_reason": "Gynecological conditions and female reproductive health evaluations."
    },
    {
        "code": "GEN_MED",
        "name": "General Medicine",
        "keywords": [
            r"\bfever\b", r"\bcold\b", r"\bflu\b", r"\bweakness\b", r"\btired\b", r"\bfatigue\b",
            r"\bgeneral checkup\b", r"\bannual exam\b", r"\bweight loss\b", r"\bchills\b",
            r"\bbody ache\b", r"\bvital check\b", r"\bdiabetes check\b"
        ],
        "priority": 1,
        "base_reason": "Systemic constitutional symptoms or general adult medical consultation."
    }
]

class TriageRouterPlugin:
    """
    Microsoft Semantic Kernel Plugin for Triage Router Agent.
    Contains real Python tools for department classification and catalogue validation.
    """

    def __init__(self, agent: "TriageRouterAgent"):
        self.agent = agent

    @kernel_function(
        name="classify_patient_concern",
        description="Analyzes the described concern against hospital department rules, returning suggested department, reason, and confidence score."
    )
    def classify_patient_concern(
        self,
        described_concern: str,
        age: Optional[int] = None,
        duration: Optional[str] = "",
        additional_info: Optional[str] = ""
    ) -> Dict[str, Any]:
        """Tool 1: Rule-based classification matching patient concerns to hospital departments."""
        text = f"{described_concern or ''} {additional_info or ''}".lower()
        scores = {}
        matched_rules = {}

        # Check Paediatrics age override
        if age is not None and age < 18:
            scores["PAED"] = scores.get("PAED", 0) + 40
            matched_rules["PAED"] = ["Patient is a minor under 18 years of age"]

        # Evaluate all department rule sets
        for rule in DEPARTMENT_ROUTING_RULES:
            code = rule["code"]
            rule_score = 0
            hits = []

            for pattern in rule["keywords"]:
                matches = re.findall(pattern, text)
                if matches:
                    rule_score += len(matches) * 30
                    hits.append(pattern.replace(r"\b", "").replace("(?:", "").replace(")", ""))

            if hits:
                scores[code] = scores.get(code, 0) + rule_score
                matched_rules[code] = hits

        # Rank departments by calculated score
        sorted_depts = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        if not sorted_depts:
            # Fallback to General Medicine when ambiguous
            return {
                "selected_department": "General Medicine",
                "department_code": "GEN_MED",
                "confidence_score": 0.55,
                "reason": "The described concern does not clearly single out a specialized organ system. General Medicine is recommended for an initial comprehensive clinical evaluation.",
                "alternative_department": None,
                "is_ambiguous": True
            }

        top_code, top_score = sorted_depts[0]
        alt_code = sorted_depts[1][0] if len(sorted_depts) > 1 else None

        # Compute normalized confidence score between 0.70 and 0.96 for matched rules
        confidence = min(0.96, max(0.70, round(0.70 + (top_score / 100.0) * 0.25, 2)))

        # Find department definition
        top_dept_def = next((d for d in DEPARTMENT_ROUTING_RULES if d["code"] == top_code), None)
        alt_dept_def = next((d for d in DEPARTMENT_ROUTING_RULES if d["code"] == alt_code), None) if alt_code else None

        dept_name = top_dept_def["name"] if top_dept_def else "General Medicine"
        alt_name = alt_dept_def["name"] if alt_dept_def else None

        hits_str = ", ".join(matched_rules.get(top_code, [])[:3])
        reason = (
            f"{top_dept_def['base_reason']} Key indicators mentioned: '{hits_str}'. "
            f"Evaluated with {int(confidence * 100)}% routing confidence."
        )

        return {
            "selected_department": dept_name,
            "department_code": top_code,
            "confidence_score": confidence,
            "reason": reason,
            "alternative_department": alt_name,
            "is_ambiguous": confidence < 0.65
        }

    @kernel_function(
        name="get_department_information",
        description="Retrieves official details and verifies operating status of a department from the hospital catalogue."
    )
    def get_department_information(
        self,
        department_code: str
    ) -> Dict[str, Any]:
        """Tool 2: Query database catalogue for department metadata and verification."""
        db = SessionLocal()
        try:
            dept = db.query(Department).filter(
                (Department.code == department_code) | (Department.name == department_code)
            ).first()

            if not dept:
                return {
                    "exists": False,
                    "department_code": department_code,
                    "message": f"Department '{department_code}' is not recognized in the active catalogue."
                }

            return {
                "exists": True,
                "id": dept.id,
                "code": dept.code,
                "name": dept.name,
                "description": dept.description,
                "location": dept.location,
                "operating_hours": dept.operating_hours,
                "contact_phone": dept.contact_phone
            }
        finally:
            db.close()


class TriageRouterAgent(BaseAgent):
    """
    Agent 2: Triage Router Agent.
    Routes patient complaints to the appropriate hospital department using clinical classification rules.
    Never names a disease or provides a diagnosis.
    """

    def __init__(self):
        super().__init__(
            agent_name="Triage Router Agent",
            description="Analyzes patient concern and assigns the most suitable hospital clinical department."
        )
        self.plugin = TriageRouterPlugin(self)
        self.kernel.add_plugin(self.plugin, plugin_name="TriageRouterPlugin")

    def run(
        self,
        described_concern: str,
        age: Optional[int] = None,
        duration: Optional[str] = "",
        additional_info: Optional[str] = "",
        execution_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes classification and department verification workflow.
        """
        exec_id = execution_id or f"exec-{uuid.uuid4().hex[:8]}"
        start_time = time.time()
        self.create_execution_record(
            execution_id=exec_id,
            session_id=session_id,
            input_summary=f"Concern: '{described_concern[:60]}...' (Age: {age})"
        )

        try:
            # Step 1: Tool 1 execution - classify_patient_concern
            classification = self.plugin.classify_patient_concern(
                described_concern=described_concern,
                age=age,
                duration=duration,
                additional_info=additional_info
            )
            self.log_tool_run(
                execution_id=exec_id,
                tool_name="classify_patient_concern",
                input_args={"described_concern": described_concern, "age": age},
                output_result=classification,
                is_success=True
            )

            # Step 2: Tool 2 execution - get_department_information
            dept_info = self.plugin.get_department_information(
                department_code=classification["department_code"]
            )
            self.log_tool_run(
                execution_id=exec_id,
                tool_name="get_department_information",
                input_args={"department_code": classification["department_code"]},
                output_result=dept_info,
                is_success=dept_info["exists"]
            )

            duration_ms = (time.time() - start_time) * 1000
            summary = f"Routed to {classification['selected_department']} (Confidence: {classification['confidence_score']})"
            self.update_execution_record(
                execution_id=exec_id,
                status="COMPLETED",
                output_summary=summary,
                duration_ms=duration_ms
            )

            return {
                "success": True,
                "execution_id": exec_id,
                "tools_executed": ["classify_patient_concern", "get_department_information"],
                "data": {
                    "selected_department": classification["selected_department"],
                    "department_code": classification["department_code"],
                    "confidence_score": classification["confidence_score"],
                    "reason": classification["reason"],
                    "alternative_department": classification["alternative_department"],
                    "is_ambiguous": classification["is_ambiguous"],
                    "department_details": dept_info
                }
            }

        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self.update_execution_record(
                execution_id=exec_id,
                status="FAILED",
                output_summary="Failed triage routing",
                duration_ms=duration_ms,
                error_details=str(e)
            )
            return {
                "success": False,
                "execution_id": exec_id,
                "errors": [str(e)],
                "data": {
                    "selected_department": "General Medicine",
                    "department_code": "GEN_MED",
                    "confidence_score": 0.50,
                    "reason": "Routing system encountered an error; assigned to General Medicine for safety.",
                    "alternative_department": None,
                    "is_ambiguous": True
                }
            }
