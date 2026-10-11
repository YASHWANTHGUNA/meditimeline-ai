import os
import uuid
import asyncio
import hashlib
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional

import certifi
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

load_dotenv()

from services import extract_timeline_from_chunks
from timeline_engine import process_timeline_events
from pdf_parser import (
    parse_pdf, pages_from_text, build_chunks, locate_source,
    PdfParseError, ParsedPage,
)

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URI, tlsCAFile=certifi.where())
db = client.meditimeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.documents.create_index([("patient_id", 1), ("content_hash", 1)], unique=True)
    await db.events.create_index([("patient_id", 1)])
    yield


app = FastAPI(title="MediTimeline AI API", lifespan=lifespan)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ParseRequest(BaseModel):
    text: str
    patient_id: Optional[str] = None


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


async def _ingest(provided_patient_id: Optional[str], pages: List[ParsedPage], content_hash: str,
                  source_type: str, document_name: str):
    # 1. Extract with Gemini first
    chunks = build_chunks(pages)
    try:
        extraction = await extract_timeline_from_chunks(chunks)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e

    meta = extraction.get("metadata") or {}
    auto_extracted_pid = meta.get("patient_id")
    
    # Hierarchy: AI Extracted > Form Provided > Default Fallback
    patient_id = auto_extracted_pid if auto_extracted_pid else (provided_patient_id or "P001")

    # 2. Exact File Deduplication (With Orphan Cleanup)
    existing = await db.documents.find_one(
        {"patient_id": patient_id, "content_hash": content_hash}, {"_id": 0}
    )
    if existing:
        # Check if events actually exist for this patient
        event_count = await db.events.count_documents({"patient_id": patient_id})
        if event_count > 0:
            result = await get_patient_timeline(patient_id)
            result["message"] = f"This document was already processed for patient {patient_id}."
            result["duplicate"] = True
            return result
        else:
            # Clean up orphaned document from a previously failed run
            await db.documents.delete_one({"patient_id": patient_id, "content_hash": content_hash})

    raw_events = extraction.get("events", [])
    if not raw_events:
        return {
            "message": "No clinical events were extracted from this document.",
            "patient_id": patient_id,
            "timeline": process_timeline_events([]),
        }

    document_id = f"doc_{uuid.uuid4().hex[:12]}"
    await db.documents.insert_one({
        "document_id": document_id,
        "patient_id": patient_id,
        "patient_name": meta.get("patient_name"),
        "document_name": document_name,
        "source_type": source_type,
        "page_count": len(pages),
        "uploaded_at": datetime.now(timezone.utc),
        "content_hash": content_hash,
        "event_count": len(raw_events),
    })

    # 3. Database-Level Semantic Deduplication
    existing_events = await db.events.find(
        {"patient_id": patient_id}, 
        {"event_type": 1, "title": 1, "date": 1, "original_date_str": 1, "_id": 0}
    ).to_list(length=None)
    
    seen_keys = set()
    for ev in existing_events:
        key = (
            ev.get("event_type"),
            (ev.get("title") or "").strip().lower(),
            ev.get("date") or ev.get("original_date_str") or ""
        )
        seen_keys.add(key)

    # 4. Verify provenance & filter duplicates
    to_insert = []
    for event in raw_events:
        key = (
            event.get("event_type"),
            (event.get("title") or "").strip().lower(),
            event.get("date") or event.get("original_date_str") or ""
        )
        
        if key in seen_keys:
            continue
            
        seen_keys.add(key)
        
        src = event.get("source") or {}
        page, verified = locate_source(src.get("source_text"), pages)
        event["source"] = {
            **src,
            "document_id": document_id,
            "document_name": document_name,
            "page": page,
            "verified": verified,
        }
        event["patient_id"] = patient_id
        event["event_id"] = f"evt_{uuid.uuid4().hex[:12]}"
        to_insert.append(event)

    if to_insert:
        await db.events.insert_many(to_insert)
        
    return await get_patient_timeline(patient_id)


@app.post("/api/parse-report")
async def parse_report(request: ParseRequest):
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    pages = pages_from_text(request.text)
    return await _ingest(
        provided_patient_id=request.request.patient_id if hasattr(request, 'request') else request.patient_id,
        pages=pages,
        content_hash=_sha256(request.text.strip().encode("utf-8")),
        source_type="text_paste",
        document_name="Pasted text",
    )


@app.post("/api/upload-report")
async def upload_report(
    file: UploadFile = File(...), 
    patient_id: Optional[str] = Form(None)
):
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="PDF is too large (max 10 MB).")

    try:
        parsed = await asyncio.to_thread(parse_pdf, data)
    except PdfParseError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    return await _ingest(
        provided_patient_id=patient_id,
        pages=parsed.pages,
        content_hash=_sha256(data),
        source_type="pdf_upload",
        document_name=file.filename,
    )


@app.get("/patients/{patient_id}/timeline")
async def get_patient_timeline(patient_id: str):
    events = await db.events.find({"patient_id": patient_id}, {"_id": 0}).to_list(length=None)
    
    # Process the events using the timeline engine
    result = process_timeline_events(events)
    
    # Inject the patient ID so the React frontend can display it
    result["patient_id"] = patient_id 
    
    return result
