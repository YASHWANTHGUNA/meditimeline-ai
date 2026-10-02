from pydantic import BaseModel, Field
from typing import List, Literal, Optional

class TimelineEvent(BaseModel):
    date: str = Field(..., description="Date of the event in YYYY-MM-DD format or clinical timeframe")
    event_type: Literal["Diagnosis", "Medication", "Lab Result", "Hospital Visit", "Procedure"]
    title: str = Field(..., description="Short, clear title of the clinical event")
    description: str = Field(..., description="Detailed explanation of the findings, values, or clinical notes")
    abnormal: bool = Field(False, description="True if lab results or findings are outside normal clinical ranges")
    medications: List[str] = Field(default_factory=list, description="Associated medications mentioned in this event")

class ReportParseRequest(BaseModel):
    patient_id: str
    report_text: str

class TimelineResponse(BaseModel):
    patient_id: str
    events: List[TimelineEvent]
    raw_text: Optional[str] = None