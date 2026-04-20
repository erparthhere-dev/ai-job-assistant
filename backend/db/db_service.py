import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from db.models import ResumeDB, JobSearchDB, JobMatchDB
from models.schemas import ResumeParseResponse, JobSearchResponse

logger = logging.getLogger(__name__)


# ── Resume Operations ─────────────────────────────────────────────────────────

async def save_resume(db: AsyncSession, resume: ResumeParseResponse, embedding: list[float]) -> None:
    """Save parsed resume and its embedding to database."""
    db_resume = ResumeDB(
        resume_id=       resume.resume_id,
        raw_text=        resume.raw_text,
        skills=          resume.skills,
        experience_years=resume.experience_years,
        education=       resume.education,
        job_titles=      resume.job_titles,
        summary=         resume.summary,
        chunk_count=     resume.chunk_count,
        embedding=       embedding,
        created_at=      datetime.utcnow(),
    )
    db.add(db_resume)
    await db.commit()
    logger.info(f"Resume saved to DB: {resume.resume_id}")


async def get_resume_from_db(db: AsyncSession, resume_id: str) -> ResumeDB | None:
    """Retrieve resume from database by ID."""
    result = await db.execute(
        select(ResumeDB).where(ResumeDB.resume_id == resume_id)
    )
    return result.scalar_one_or_none()


async def get_resume_embedding(db: AsyncSession, resume_id: str) -> list[float] | None:
    """Retrieve resume embedding from database."""
    db_resume = await get_resume_from_db(db, resume_id)
    if db_resume and db_resume.embedding:
        logger.info(f"Embedding loaded from DB for resume: {resume_id}")
        return db_resume.embedding
    return None


# ── Job Search Operations ─────────────────────────────────────────────────────

async def save_job_search(
    db: AsyncSession,
    resume_id: str,
    query: str,
    location: str,
    remote_only: bool,
    top_k: int,
    total_jobs: int,
) -> str:
    """Save job search record and return search_id."""
    search_id = str(uuid.uuid4())
    db_search = JobSearchDB(
        search_id=          search_id,
        resume_id=          resume_id,
        query=              query,
        location=           location,
        remote_only=        str(remote_only),
        top_k=              top_k,
        total_jobs_fetched= total_jobs,
        created_at=         datetime.utcnow(),
    )
    db.add(db_search)
    await db.commit()
    logger.info(f"Job search saved to DB: {search_id}")
    return search_id


async def save_job_matches(
    db: AsyncSession,
    search_id: str,
    matches: list,
) -> None:
    """Save all job matches for a search."""
    for match in matches:
        db_match = JobMatchDB(
            match_id=       str(uuid.uuid4()),
            search_id=      search_id,
            job_id=         match.job.job_id,
            title=          match.job.title,
            company=        match.job.company,
            location=       match.job.location,
            source=         match.job.source,
            apply_link=     match.job.apply_link,
            match_score=    match.match_score,
            match_reasons=  match.match_reasons,
            missing_skills= match.missing_skills,
            cover_letter=   match.cover_letter,
            created_at=     datetime.utcnow(),
        )
        db.add(db_match)
    await db.commit()
    logger.info(f"Saved {len(matches)} matches for search: {search_id}")