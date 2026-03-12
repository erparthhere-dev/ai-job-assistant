from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# ── Resume Models ─────────────────────────────────────────────────────────────

class ResumeParseResponse(BaseModel):
    resume_id: str
    raw_text: str
    skills: list[str]
    experience_years: Optional[float] = None
    education: list[str]
    job_titles: list[str]
    summary: str
    chunk_count: int
    processed_at: datetime = Field(default_factory=datetime.utcnow)


# ── Job Models ────────────────────────────────────────────────────────────────

class JobPosting(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    description: str
    apply_link: Optional[str] = None
    posted_at: Optional[str] = None
    employment_type: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    remote: bool = False


class JobMatch(BaseModel):
    job: JobPosting
    match_score: float = Field(ge=0.0, le=1.0)
    match_reasons: list[str]
    missing_skills: list[str]
    cover_letter: Optional[str] = None


# ── API Request/Response Models ───────────────────────────────────────────────

class JobSearchRequest(BaseModel):
    resume_id: str
    query: Optional[str] = None
    location: Optional[str] = None
    remote_only: bool = False
    top_k: int = Field(default=5, ge=1, le=20)


class JobSearchResponse(BaseModel):
    resume_id: str
    total_jobs_fetched: int
    matches: list[JobMatch]
    searched_at: datetime = Field(default_factory=datetime.utcnow)


class CoverLetterRequest(BaseModel):
    resume_id: str
    job_id: str
    tone: str = Field(default="professional")


class CoverLetterResponse(BaseModel):
    resume_id: str
    job_id: str
    cover_letter: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# ── Error Models ──────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None