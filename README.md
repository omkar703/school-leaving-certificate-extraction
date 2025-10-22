# School Leaving Certificate Data Extractor API

A FastAPI service that extracts two fields from a School Leaving Certificate image using Groq Llama 4 Scout in JSON Mode:
- school_name
- last_class_attended

Requirements:
- Python 3.9+
- Environment variable: GROQ_API_KEY

Run locally:
1) python3 -m venv .venv
2) . .venv/bin/activate
3) pip install -r requirements.txt
4) export GROQ_API_KEY={{GROQ_API_KEY}}
5) uvicorn main:app --reload

Endpoint:
- POST /api/v1/extract_certificate_data (multipart/form-data, field: file)
- GET /health
