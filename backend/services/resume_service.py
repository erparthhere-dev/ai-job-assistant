import uuid
import json
import logging
from typing import Optional

import fitz  # PyMuPDF
from openai import AsyncOpenAI

from core.config import get_settings
from models.schemas import ResumeParseResponse

logger = logging.getLogger(__name__)
settings = get_settings()


# ── In-memory resume store ────────────────────────────────────────────────────
_resume_store: dict[str, ResumeParseResponse] = {}


def get_resume(resume_id: str) -> Optional[ResumeParseResponse]:
    return _resume_store.get(resume_id)


def store_resume(resume: ResumeParseResponse) -> None:
    _resume_store[resume.resume_id] = resume


# ── PDF Text Extraction ───────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text_parts = []
    with fitz.open(stream=file_bytes, filetype="pdf") as doc:
        for page in doc:
            text_parts.append(page.get_text("text"))
    full_text = "\n".join(text_parts).strip()
    if not full_text:
        raise ValueError("Could not extract text from PDF. The file may be scanned or image-based.")
    logger.info(f"Extracted {len(full_text)} characters from PDF ({len(text_parts)} pages)")
    return full_text


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


# ── LLM Resume Extraction ─────────────────────────────────────────────────────

EXTRACTION_PROMPT = """
You are a resume parser. Extract structured information from the resume text below.

Return ONLY valid JSON with this exact structure:
{{
  "skills": ["skill1", "skill2", ...],
  "experience_years": <number or null>,
  "education": ["degree and institution", ...],
  "job_titles": ["most recent title", ...],
  "summary": "2-3 sentence professional summary of this candidate"
}}

Rules:
- skills: technical and soft skills (max 20)
- experience_years: total years of work experience as a float
- education: list of degrees with institutions
- job_titles: list of job titles held (most recent first, max 5)
- summary: concise professional summary

Resume text:
{resume_text}
"""

async def extract_resume_structure(raw_text: str) -> dict:
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    truncated = raw_text[:6000]

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "user",
                "content": EXTRACTION_PROMPT.format(resume_text=truncated)
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.1,
    )

    content = response.choices[0].message.content
    return json.loads(content)


# ── Main Service Function ─────────────────────────────────────────────────────

async def parse_resume(file_bytes: bytes, filename: str) -> ResumeParseResponse:
    logger.info(f"Parsing resume: {filename}")

    raw_text = extract_text_from_pdf(file_bytes)
    chunks = chunk_text(raw_text)
    logger.info(f"Created {len(chunks)} text chunks")

    structured = await extract_resume_structure(raw_text)

    resume = ResumeParseResponse(
        resume_id=str(uuid.uuid4()),
        raw_text=raw_text,
        skills=structured.get("skills", []),
        experience_years=structured.get("experience_years"),
        education=structured.get("education", []),
        job_titles=structured.get("job_titles", []),
        summary=structured.get("summary", ""),
        chunk_count=len(chunks),
    )

    store_resume(resume)
    logger.info(f"Resume stored with ID: {resume.resume_id}")
    return resume