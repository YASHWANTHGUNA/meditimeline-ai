import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv
from schemas import TimelineEvent

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Initialize the official Google GenAI SDK client
client = genai.Client(api_key=GEMINI_API_KEY)

def extract_timeline_from_text(report_text: str) -> list[TimelineEvent]:
    """
    Sends medical report text to Gemini 2.5 Flash and forces a structured 
    JSON response conforming to our clinical event schema.
    """
    prompt = f"""
    You are an expert clinical data extraction assistant. 
    Analyze the following medical report and extract all clinical events into a structured chronological list.
    
    Classify each event into one of these exact types:
    - Diagnosis
    - Medication
    - Lab Result
    - Hospital Visit
    - Procedure
    
    If test results are outside normal limits, set 'abnormal' to true.
    Extract any relevant medications mentioned into the 'medications' list.

    Medical Report Text:
    {report_text}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=list[TimelineEvent],
                temperature=0.1 # Low temperature for clinical accuracy
            ),
        )
        
        # Parse the structured JSON output into validated Pydantic models
        events_data = json.loads(response.text)
        validated_events = [TimelineEvent(**event) for event in events_data]
        return validated_events

    except Exception as e:
        raise RuntimeError(f"AI extraction failed: {str(e)}")