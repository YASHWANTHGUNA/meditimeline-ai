import asyncio
import json
import os
from typing import Dict, List, Optional

from google import genai
from google.genai import types
from schemas import ExtractionResponse

client = genai.Client()
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

MAX_CONCURRENT_CALLS = 1
_semaphore = asyncio.Semaphore(MAX_CONCURRENT_CALLS)

PROMPT = """
You are an expert clinical data extractor. Analyze the medical record text below
and extract patient demographic metadata along with all clinically significant events into a structured timeline.

Identify and extract:
1. Patient Metadata: Look in the document header for Patient ID (e.g. PT-8472-X, P001) and Patient Name.
2. Diagnoses and conditions.
3. Medications (dose, frequency, and changes like 'increased' or 'stopped').
4. Laboratory results (values, units, reference ranges; flag abnormal results).
5. Procedures, hospital visits, and significant symptoms.
6. Family History (use event_type "Family History"; include relative and age of onset if given).

Rules:
- Extract ONLY information explicitly present in the text. Do NOT infer or invent anything.
- Keep the exact date as written in original_date_str. If no date is stated, leave date null.
  If the document header gives a single report/visit date and an item clearly belongs to that visit, you may use it.
- Flag abnormal labs using the reference range in the text, or the status the report itself states.
- source_text MUST be a short VERBATIM quote copied character-for-character from the text below
  (max ~200 characters). Never paraphrase it.
- The text contains markers like "--- PAGE 2 ---". Do not output page numbers; the server handles that.
- Do not create duplicate events for the same fact.

Medical Text:
{text}
"""

async def _extract_chunk(chunk: str) -> dict:
    async with _semaphore:
        response = await client.aio.models.generate_content(
            model=DEFAULT_MODEL,
            contents=PROMPT.format(text=chunk),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExtractionResponse,
                temperature=0.1,
            ),
        )
    if response.parsed:
        return response.parsed.model_dump()
    return json.loads(response.text)


def _dedupe(events: List[dict]) -> List[dict]:
    """Chunks can overlap semantically; drop exact repeats of the same fact."""
    seen, out = set(), []
    for e in events:
        key = (
            e.get("event_type"),
            (e.get("title") or "").strip().lower(),
            e.get("date") or e.get("original_date_str") or "",
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out


async def extract_timeline_from_chunks(chunks: List[str]) -> Dict:
    """Runs Gemini over every chunk concurrently and merges the results."""
    try:
        results = await asyncio.gather(*[_extract_chunk(c) for c in chunks])
    except Exception as e:
        print(f"Error during Gemini extraction: {e}")
        raise RuntimeError(
            "Medical report extraction failed. Gemini may be temporarily "
            "unavailable. Please try again shortly."
        ) from e

    merged_events = []
    extracted_pid = None
    extracted_pname = None

    for res in results:
        merged_events.extend(res.get("events", []))
        meta = res.get("metadata") or {}
        if not extracted_pid and meta.get("patient_id"):
            extracted_pid = meta.get("patient_id")
        if not extracted_pname and meta.get("patient_name"):
            extracted_pname = meta.get("patient_name")

    return {
        "metadata": {
            "patient_id": extracted_pid,
            "patient_name": extracted_pname
        },
        "events": _dedupe(merged_events)
    }


async def extract_timeline_from_text(text: str) -> Dict:
    """Backwards-compatible helper for pasted text."""
    return await extract_timeline_from_chunks([text])