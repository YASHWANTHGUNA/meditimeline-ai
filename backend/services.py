import asyncio
import json
import os
import random
from typing import Dict, List

from google import genai
from google.genai import types, errors
from schemas import ExtractionResponse

client = genai.Client()

PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
# Tried in order when the primary model is overloaded (503) or rate limited (429).
FALLBACK_MODELS = [
    m.strip()
    for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-2.5-flash-lite,gemini-2.0-flash").split(",")
    if m.strip()
]
MODEL_CHAIN = [PRIMARY_MODEL] + [m for m in FALLBACK_MODELS if m != PRIMARY_MODEL]

RETRIES_PER_MODEL = int(os.getenv("GEMINI_RETRIES", "3"))
BASE_DELAY = 1.5  # seconds; doubles each attempt, plus jitter
RETRYABLE_CODES = {429, 500, 502, 503, 504}

MAX_CONCURRENT_CALLS = int(os.getenv("GEMINI_CONCURRENCY", "2"))
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
7. Vital signs (blood pressure, heart rate, SpO2, temperature, BMI, weight): use event_type "Vital Sign" (NOT "Other")
   and fill the lab object: test_name, value (numeric if single number), value_text (e.g. "128/82"), unit,
   reference_low/high when numeric, and status. Set abnormal=true only if the report flags it or it is outside its range.

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


def _config() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ExtractionResponse,
        temperature=0.1,
    )


async def _call_model(model: str, chunk: str) -> dict:
    response = await client.aio.models.generate_content(
        model=model, contents=PROMPT.format(text=chunk), config=_config()
    )
    if response.parsed:
        return response.parsed.model_dump()
    return json.loads(response.text)


async def _extract_chunk(chunk: str) -> dict:
    """Retry with exponential backoff + jitter, then fall back to the next model."""
    last_err: Exception | None = None
    for model in MODEL_CHAIN:
        for attempt in range(RETRIES_PER_MODEL):
            try:
                async with _semaphore:
                    result = await _call_model(model, chunk)
                if model != PRIMARY_MODEL:
                    print(f"[gemini] served by fallback model {model}")
                return result
            except errors.APIError as e:
                last_err = e
                code = getattr(e, "code", None)
                if code == 404:          # model not available to this key -> next model
                    break
                if code not in RETRYABLE_CODES:
                    raise                # 400/401/403: retrying won't help
                delay = BASE_DELAY * (2 ** attempt) + random.uniform(0, 1)
                print(f"[gemini] {model} {code} (attempt {attempt + 1}/{RETRIES_PER_MODEL}); retry in {delay:.1f}s")
                await asyncio.sleep(delay)
            except (json.JSONDecodeError, ValueError) as e:
                last_err = e             # malformed JSON: one more try is usually enough
                await asyncio.sleep(BASE_DELAY)
    raise last_err or RuntimeError("Gemini extraction failed")


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
    """Runs Gemini over every chunk concurrently (bounded) and merges the results."""
    try:
        results = await asyncio.gather(*[_extract_chunk(c) for c in chunks])
    except Exception as e:
        print(f"Error during Gemini extraction (all models/retries exhausted): {e}")
        raise RuntimeError(
            "The AI service is overloaded right now. We retried and tried backup models, "
            "but none responded. Please try again in a minute."
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
        "metadata": {"patient_id": extracted_pid, "patient_name": extracted_pname},
        "events": _dedupe(merged_events),
    }


async def extract_timeline_from_text(text: str) -> Dict:
    """Backwards-compatible helper for pasted text."""
    return await extract_timeline_from_chunks([text])