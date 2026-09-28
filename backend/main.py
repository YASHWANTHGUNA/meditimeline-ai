from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pydantic import BaseModel
from services import parse_medical_report

load_dotenv()

app = FastAPI(title="MediTimeline-AI API", version="1.0")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MONGO_URI = os.getenv("MONGO_URI")
client_db = AsyncIOMotorClient(MONGO_URI)
db = client_db.meditimeline

class ReportRequest(BaseModel):
    patient_id: str
    report_text: str

@app.get("/")
async def root():
    return {"message": "MediTimeline-AI Backend is running successfully!"}

@app.get("/health")
async def health_check():
    try:
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/parse-report")
async def parse_and_save_report(data: ReportRequest):
    # 1. Call Gemini to parse unstructured text into structured timeline events
    parsed_json_str = await parse_medical_report(data.report_text)
    
    # 2. Save raw text and parsed result to MongoDB Atlas
    record = {
        "patient_id": data.patient_id,
        "raw_text": data.report_text,
        "timeline_data": parsed_json_str
    }
    
    result = await db.reports.insert_one(record)
    
    return {
        "status": "success",
        "record_id": str(result.inserted_id),
        "timeline": parsed_json_str
    }
    