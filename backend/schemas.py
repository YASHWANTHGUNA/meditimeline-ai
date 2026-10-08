from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class LabMeasurement(BaseModel):
    test_name: str = Field(..., description="Name of the laboratory test (e.g., HbA1c, Fasting Glucose)")
    value: Optional[float] = Field(None, description="Numeric value of the result if applicable")
    value_text: Optional[str] = Field(None, description="Text representation of the result if not purely numeric")
    unit: Optional[str] = Field(None, description="Unit of measurement (e.g., mg/dL, %)")
    reference_low: Optional[float] = Field(None, description="Lower bound of the normal reference range")
    reference_high: Optional[float] = Field(None, description="Upper bound of the normal reference range")
    status: Literal["normal", "high", "low", "critical", "unknown"] = "unknown"

class MedicationInfo(BaseModel):
    name: str = Field(..., description="Generic or brand name of the medication")
    dose: Optional[str] = Field(None, description="Dosage amount (e.g., 500 mg, 10 mg/mL)")
    frequency: Optional[str] = Field(None, description="Frequency (e.g., once daily, BID, PRN)")
    route: Optional[str] = Field(None, description="Route of administration (e.g., Oral, IV)")
    action: Optional[Literal[
        "started",
        "continued",
        "stopped",
        "increased",
        "decreased",
        "changed",
        "unknown"
    ]] = "unknown"

class SourceReference(BaseModel):
    document_id: Optional[str] = Field(None, description="Unique ID of the source document")
    document_name: Optional[str] = Field(None, description="Filename or title of the document")
    page: Optional[int] = Field(None, description="Page number where the event was found")
    source_text: Optional[str] = Field(None, description="The exact sentence or snippet from the original document")

class TimelineEvent(BaseModel):
    event_id: str = Field(..., description="Unique identifier for this specific event")
    patient_id: Optional[str] = Field(None, description="Identifier for the patient")
    date: Optional[str] = Field(None, description="Normalized date string in YYYY-MM-DD or YYYY-MM format. Null if undated.")
    original_date_str: Optional[str] = Field(None, description="The raw date string as written in the report")
    event_type: Literal["Diagnosis", "Medication", "Lab Result", "Procedure", "Symptom", "Visit", "Other"]
    title: str = Field(..., description="Concise summary title of the event")
    description: str = Field(..., description="Detailed description or clinical context")
    abnormal: bool = Field(False, description="Flag indicating if the event represents an abnormal finding")
    
    # Structured Clinical Details
    lab: Optional[LabMeasurement] = None
    medication: Optional[MedicationInfo] = None
    
    # Traceability
    source: Optional[SourceReference] = None

class ExtractionResponse(BaseModel):
    events: List[TimelineEvent] = Field(default_factory=list, description="List of extracted timeline events from the medical text")