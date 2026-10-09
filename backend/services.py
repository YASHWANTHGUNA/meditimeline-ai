import os
from google import genai
from google.genai import types
from schemas import ExtractionResponse

# Initialize the modern GenAI client
client = genai.Client()
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

async def extract_timeline_from_text(text: str) -> dict:
    """
    Analyzes unstructured medical text and extracts a structured timeline of clinical events.
    Uses the async client to avoid blocking the FastAPI event loop.
    """
    prompt = f"""
    You are an expert clinical data extractor. Analyze the following medical record text
    and extract all clinically significant events into a structured timeline.

    Identify and extract:
    1. Diagnoses and conditions.
    2. Medications (including dose, frequency, and changes like 'increased' or 'stopped').
    3. Laboratory results (include values, units, reference ranges, and flag abnormal results).
    4. Procedures, hospital visits, and significant symptoms.
    5. Family History (including relatives' conditions and age of onset).

    Important Instructions:
    - CRITICAL: Extract ONLY information explicitly present in the source text.
    - DO NOT hallucinate, infer, or invent patient history, dates, medications, or events.
    - Retain the exact date or timeframe mentioned. If a detail (like a specific date) is missing, leave it null. Do not guess.
    - Accurately flag abnormal lab results based on provided text or standard reference ranges.
    - Extract precise source text snippets that support your extraction.
    
    Medical Text:
    {text}
    """
    
    try:
        # Utilize the async client (.aio) and enforce the Pydantic schema output
        response = await client.aio.models.generate_content(
            model=DEFAULT_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ExtractionResponse,
                temperature=0.1 # Low temperature for deterministic, factual extraction
            )
        )
        
        # The new SDK parses the JSON automatically into the Pydantic model
        if response.parsed:
            return response.parsed.model_dump()
        else:
            # Fallback if parsed is empty but text exists
            import json
            return json.loads(response.text)
            
    except Exception as e:
        print(f"Error during Gemini extraction: {e}")
        raise RuntimeError(
            "Medical report extraction failed. Gemini may be temporarily "
             "unavailable. Please try again shortly."
             ) from e