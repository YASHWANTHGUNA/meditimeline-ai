import os
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import Optional

from services import extract_timeline_from_text
from timeline_engine import process_timeline_events

app = FastAPI(title="MediTimeline AI API")

# Secure CORS configuration
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URI)
db = client.meditimeline

class ParseRequest(BaseModel):
    text: str
    patient_id: str = "P001"  # Defaulting for now until auth/patient-selection is built

@app.post("/api/parse-report")
async def parse_report(request: ParseRequest):
    """
    Ingests medical text, extracts structured events using Gemini, 
    normalizes them, and stores them in the patient's record.
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    # 1. Extract structured events using Gemini
    extraction_result = await extract_timeline_from_text(request.text)
    raw_events = extraction_result.get("events", [])

    if not raw_events:
        return {"message": "No events extracted.", "timeline": {}}

    document_id = f"doc_{uuid.uuid4().hex[:12]}"
    current_time = datetime.utcnow()

    # 2. Store document metadata
    await db.documents.insert_one({
        "document_id": document_id,
        "patient_id": request.patient_id,
        "source_type": "text_paste",
        "uploaded_at": current_time,
        "content_hash": hash(request.text) # Basic hash for deduplication logic later
    })

    # 3. Attach provenance and patient ID to each event before saving
    events_to_insert = []
    for event in raw_events:
        event["patient_id"] = request.patient_id
        event["event_id"] = f"evt_{uuid.uuid4().hex[:12]}"
        
        # Ensure source object exists
        if "source" not in event or not event["source"]:
            event["source"] = {}
        event["source"]["document_id"] = document_id
        
        events_to_insert.append(event)

    # 4. Save to events collection
    if events_to_insert:
        await db.events.insert_many(events_to_insert)

    # 5. Fetch all events for this patient and return the merged timeline
    return await get_patient_timeline(request.patient_id)

@app.get("/patients/{patient_id}/timeline")
async def get_patient_timeline(patient_id: str):
    """
    Fetches all clinical events for a specific patient across all documents,
    sorts them chronologically, and returns the unified timeline.
    """
    cursor = db.events.find({"patient_id": patient_id}, {"_id": 0})
    all_patient_events = await cursor.to_list(length=1000)

    if not all_patient_events:
        return {"patient_id": patient_id, "timeline": {}}

    # Process, normalize dates, and sort deterministically
    timeline_data = process_timeline_events(all_patient_events)

    return {
        "patient_id": patient_id,
        "timeline": timeline_data
    }