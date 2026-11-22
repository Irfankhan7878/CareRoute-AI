from pydantic import BaseModel, Field, field_validator
from typing import Optional
import datetime

class IntakeRequest(BaseModel):
    patient_name: str = Field(..., min_length=2, max_length=100, description="Full name or identifier of the patient")
    age: int = Field(..., ge=0, le=120, description="Patient age in years (0-120)")
    described_concern: str = Field(..., min_length=3, max_length=1000, description="Patient's described symptoms or medical concern")
    duration: Optional[str] = Field("Unspecified", max_length=100, description="Duration of symptoms (e.g., '3 days', '2 weeks')")
    additional_info: Optional[str] = Field(None, max_length=1000, description="Any past history or medications")
    is_returning_patient: bool = Field(False, description="Flag indicating if the patient has visited previously")
    patient_id: Optional[str] = Field(None, description="Existing patient ID if returning")

    @field_validator("patient_name")
    def clean_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Patient name cannot be blank")
        return v

    @field_validator("described_concern")
    def clean_concern(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Described concern cannot be empty")
        return v

class IntakeResponse(BaseModel):
    session_id: str
    patient_id: str
    patient_name: str
    age: int
    described_concern: str
    duration: Optional[str]
    is_returning_patient: bool
    status: str
    created_at: datetime.datetime
