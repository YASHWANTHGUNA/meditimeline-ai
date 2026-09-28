import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

# Initialize the new Google GenAI client
client = genai.Client(api_key=api_key)

async def parse_medical_report(report_text: str):
    prompt = f"""
    You are an expert clinical data extractor. Analyze the following medical report text and extract a structured chronological timeline of events.
    Return ONLY a valid JSON array of objects. Each object must have these exact keys:
    - "date": Date of the event (YYYY-MM-DD or string if exact date is unknown)
    - "event_type": One of ["Diagnosis", "Medication", "Lab Result", "Hospital Visit", "Procedure"]
    - "title": Short title of the event
    - "description": Summary of the findings or changes
    - "abnormal": Boolean (true if any lab value or finding is abnormal, otherwise false)
    - "medications": List of strings (any medications prescribed or updated, else empty list)

    Medical Report Text:
    {report_text}
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return response.text
    except Exception as e:
        return {"error": str(e)}