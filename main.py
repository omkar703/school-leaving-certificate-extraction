import os
import base64
import json
import logging
from typing import Literal

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from groq import Groq

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("certificate_extractor")

# Pydantic models
class CertificateExtraction(BaseModel):
    """Schema for the extracted data from the certificate."""
    school_name: str = Field(..., description="The full, official name of the school or institution.")
    last_class_attended: str = Field(
        ..., description="The last class, standard, or grade the student was in (e.g., '10th Standard', 'Class XII', 'Grade 12')."
    )

class ExtractionResponse(BaseModel):
    """The complete response structure."""
    status: Literal["success"] = "success"
    data: CertificateExtraction

# FastAPI app
app = FastAPI(
    title="School Leaving Certificate Data Extractor API",
    version="1.0.0",
    description=(
        "Extracts School Name and Last Class/Standard Attended from an uploaded School Leaving Certificate image "
        "using Groq Llama 4 Scout in JSON Mode."
    ),
)

# Groq client (expects GROQ_API_KEY in environment)
_groq_api_key = os.getenv("GROQ_API_KEY")
if not _groq_api_key:
    logger.warning("GROQ_API_KEY is not set. The API will start, but requests will fail until it is configured.")
client = Groq(api_key=_groq_api_key) if _groq_api_key else None

SUPPORTED_CONTENT_TYPES = {"image/jpeg", "image/png"}

SYSTEM_PROMPT = (
    "You are an expert Optical Character Recognition (OCR) and document parsing agent. "
    "Your sole function is to accurately read the provided image of a School Leaving Certificate and extract specific "
    "required data fields. You MUST return the output as a valid JSON object strictly conforming to the provided "
    "Pydantic schema. Do not include any introductory text, apologies, or explanations outside the JSON block."
)

USER_PROMPT = (
    "Analyze the uploaded School Leaving Certificate image. Identify the full, official name of the school and the "
    "last class or standard the student was present in. Return the data using the keys school_name and last_class_attended."
)


def _to_data_url(content_type: str, raw_bytes: bytes) -> str:
    b64 = base64.b64encode(raw_bytes).decode("utf-8")
    return f"data:{content_type};base64,{b64}"


@app.post("/api/v1/extract_certificate_data", response_model=ExtractionResponse)
async def extract_certificate_data(file: UploadFile = File(...)):
    # Validate file presence and type
    if file is None or not getattr(file, "filename", None):
        raise HTTPException(status_code=400, detail="No file uploaded.")
    if file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type. Please upload a JPEG or PNG image.")

    # Read file content
    try:
        content = await file.read()
    except Exception:
        logger.exception("Error reading uploaded file")
        raise HTTPException(status_code=400, detail="Failed to read uploaded file.")

    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    if client is None:
        # Fail fast if API key wasn't set at startup
        raise HTTPException(status_code=500, detail="Server is not configured. Missing GROQ_API_KEY.")

    # Prepare multimodal payload for Groq API
    data_url = _to_data_url(file.content_type, content)

    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0,
            response_format={"type": "json_object"},  # Enforce JSON Mode
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": USER_PROMPT},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                },
            ],
        )
        content_str = (completion.choices[0].message.content or "").strip()
    except Exception:
        logger.exception("Groq API call failed")
        raise HTTPException(status_code=500, detail="Internal server error.")

    # Validate and parse JSON response from LLM
    try:
        raw = json.loads(content_str)
        extracted = CertificateExtraction(**raw)
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError):
        logger.exception("LLM output validation failed. Raw response: %s", content_str)
        raise HTTPException(status_code=500, detail="Internal server error.")

    return ExtractionResponse(status="success", data=extracted)


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


if __name__ == "__main__":
    # Run with: uvicorn main:app --reload
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
