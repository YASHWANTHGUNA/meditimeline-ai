import os
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

from schemas import ReportParseRequest, TimelineResponse
from services import extract_timeline_from_text
from timeline_engine import sort_and_normalize_timeline

load_dotenv()

app = FastAPI(title="MediTimeline AI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.meditimeline

@app.get("/")
def read_root():
    return {"status": "online", "service": "MediTimeline AI Backend"}

@app.get("/health")
async def health_check():
    try:
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection failed: {str(e)}"
        )

@app.post("/api/parse-report", response_model=TimelineResponse)
async def parse_report(payload: ReportParseRequest):
    try:
        # Step 1: Extract and validate raw events via Gemini service
        raw_events = extract_timeline_from_text(payload.report_text)
        
        # Step 2: Normalize dates and sort events chronologically via Python engine
        events = sort_and_normalize_timeline(raw_events)
        
        # Step 3: Prepare document for MongoDB persistence
        timeline_doc = {
            "patient_id": payload.patient_id,
            "raw_text": payload.report_text,
            "events": [event.model_dump() for event in events]
        }
        
        # Step 4: Store in MongoDB
        await db.timelines.insert_one(timeline_doc)
        
        # Step 5: Return structured response
        return TimelineResponse(
            patient_id=payload.patient_id,
            events=events,
            raw_text=payload.report_text
        )
        
    except RuntimeError as re:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(re)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )
