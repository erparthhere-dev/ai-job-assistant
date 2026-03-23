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


# ── In-memory resume store 
_resume_store: dict[str, ResumeParseResponse] = {}


def get_resume(resume_id: str) -> Optional[ResumeParseResponse]:
    return _resume_store.get(resume_id)


def store_resume(resume: ResumeParseResponse) -> None:
    _resume_store[resume.resume_id] = resume


# ── PDF Text Extraction 

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


# ── LLM Resume Extraction 

EXTRACTION_PROMPT = """
You are an expert resume parser. Extract structured information from the resume text below.

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

SKILL_INFERENCE_PROMPT = """
You are an expert technical recruiter. Given a candidate's resume details below,
infer additional skills they LIKELY have based on their experience and domain.

Candidate details:
Job Titles: {job_titles}
Explicitly stated skills: {explicit_skills}
Experience: {experience_years} years
Education: {education}
Summary: {summary}

Return ONLY valid JSON with this exact structure:
{{
  "inferred_skills": ["skill1", "skill2", ...],
  "skill_categories": {{
    "technical": ["skill1", "skill2", ...],
    "domain": ["skill1", "skill2", ...],
    "soft": ["skill1", "skill2", ...]
  }},
  "seniority_level": "junior | mid | senior",
  "core_domain": "e.g. Cybersecurity, Web Development, Data Science"
}}

Rules:
- inferred_skills: skills strongly implied by their experience (max 10)
  e.g. if they did fraud detection → infer Python, Machine Learning, SQL
  e.g. if they did cybersecurity → infer Linux, Network Security, SIEM
  e.g. if they did web dev → infer Git, REST APIs, HTML/CSS
- Only infer skills with HIGH confidence — do not guess randomly
- skill_categories: categorize ALL skills (explicit + inferred)
- seniority_level: based on experience years and job titles
- core_domain: their primary area of expertise in 1-3 words
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


async def extract_inferred_skills(structured: dict) -> dict:
    """Use GPT to infer additional skills based on experience and domain."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "user",
                "content": SKILL_INFERENCE_PROMPT.format(
                    job_titles=", ".join(structured.get("job_titles", [])),
                    explicit_skills=", ".join(structured.get("skills", [])),
                    experience_years=structured.get("experience_years", 0),
                    education=", ".join(structured.get("education", [])),
                    summary=structured.get("summary", ""),
                )
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.2,
    )

    content = response.choices[0].message.content
    return json.loads(content)


# ── Main Service Function 

async def parse_resume(file_bytes: bytes, filename: str) -> ResumeParseResponse:
    """
    Full pipeline:
    1. Extract text from PDF
    2. Chunk text
    3. Use LLM to extract structured info
    4. Use LLM to infer additional skills
    5. Combine everything and store
    """
    logger.info(f"Parsing resume: {filename}")

    # Step 1: Extract raw text
    raw_text = extract_text_from_pdf(file_bytes)

    # Step 2: Chunk for later embedding
    chunks = chunk_text(raw_text)
    logger.info(f"Created {len(chunks)} text chunks")

    # Step 3: Basic LLM extraction
    logger.info("Running basic extraction...")
    structured = await extract_resume_structure(raw_text)

    # Step 4: Infer additional skills (2nd GPT call)
    logger.info("Running skill inference...")
    inferred = await extract_inferred_skills(structured)

    # Step 5: Combine explicit + inferred skills (deduplicated)
    explicit_skills = structured.get("skills", [])
    inferred_skills = inferred.get("inferred_skills", [])
    all_skills = list(dict.fromkeys(explicit_skills + inferred_skills))  # deduplicates while preserving order

    # Step 6: Build enriched summary with domain and seniority
    base_summary = structured.get("summary", "")
    core_domain = inferred.get("core_domain", "")
    seniority = inferred.get("seniority_level", "")
    enriched_summary = f"[{seniority.upper()} | {core_domain}] {base_summary}"

    # Step 7: Build response
    resume = ResumeParseResponse(
        resume_id=str(uuid.uuid4()),
        raw_text=raw_text,
        skills=all_skills,
        experience_years=structured.get("experience_years"),
        education=structured.get("education", []),
        job_titles=structured.get("job_titles", []),
        summary=enriched_summary,
        chunk_count=len(chunks),
    )

    store_resume(resume)
    logger.info(f"Resume stored with ID: {resume.resume_id}")
    logger.info(f"Total skills extracted: {len(all_skills)} ({len(explicit_skills)} explicit + {len(inferred_skills)} inferred)")
    return resume