"""Resume parsing service — PDF extraction + LLM structuring."""
import fitz  # PyMuPDF
import json
import logging
from openai import AsyncOpenAI

from backend.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY) if settings.OPENAI_API_KEY else None

STRUCTURING_PROMPT = """
You are an expert technical recruiter and data extractor. 
Extract structured information from the resume text provided.

CRITICAL INSTRUCTIONS:
1. SKILL EXTRACTION: Scan the ENTIRE text. Extract every technical tool, programming language, 
   framework, and library mentioned (e.g., FastAPI, Docker, PyMuPDF, React, C++, WebRTC).
2. PROJECT EXTRACTION: Identify every project. For each, summarize the 'description' 
   and extract the specific 'tech_stack' used in that project.
3. NORMALIZATION: Convert mentions like 'JS' to 'JavaScript' and 'py' to 'Python'.

Return ONLY valid JSON with this schema:
{
  "skills": ["Python", "FastAPI", ...],
  "projects": [{"title": "...", "description": "...", "tech_stack": ["...", "..."]}],
  "experience": [{"role": "...", "company": "...", "description": "..."}],
  "education": {"degree": "...", "branch": "...", "cgpa": 0.0}
}
"""


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using PyMuPDF."""
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        text = ""
        for page in doc:
            text += page.get_text("text")
        doc.close()
        return text.strip()
    except Exception as e:
        logger.error(f"PDF extraction failed: {e}")
        return ""


async def structure_resume_text(raw_text: str) -> dict:
    """Use LLM to convert raw resume text into structured JSON."""
    if not client:
        logger.warning("OpenAI API key not set — returning basic structure")
        return _basic_structure(raw_text)

    try:
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": STRUCTURING_PROMPT},
                {"role": "user", "content": raw_text[:8000]},  # Limit to avoid token overflow
            ],
            temperature=0.1,
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        return {
            "skills": result.get("skills", []),
            "projects": result.get("projects", []),
            "experience": result.get("experience", []),
            "education": result.get("education", {}),
        }
    except Exception as e:
        logger.error(f"LLM structuring failed: {e}")
        return _basic_structure(raw_text)


def _basic_structure(raw_text: str) -> dict:
    """Fallback: return raw text wrapped in minimal structure."""
    return {
        "skills": [],
        "projects": [{"title": "Resume Content", "description": raw_text[:2000], "tech_stack": []}],
        "experience": [],
        "education": {},
    }


async def process_resume(pdf_bytes: bytes) -> dict:
    """Full pipeline: PDF → text → structured JSON."""
    raw_text = extract_text_from_pdf(pdf_bytes)
    if not raw_text:
        return {"raw_text": "", "structured": _basic_structure(""), "error": "Could not extract text from PDF"}

    structured = await structure_resume_text(raw_text)
    return {"raw_text": raw_text, "structured": structured, "error": None}
