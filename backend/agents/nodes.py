import json
import logging
from openai import AsyncOpenAI
from services.openai_service import embed_text, embed_texts, cosine_similarity
from services.rapidapi_service import fetch_jobs
from models.schemas import JobMatch
from agents.state import JobSearchState
from core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Node 1: Fetch Jobs ────────────────────────────────────────────────────────

async def node_fetch_jobs(state: JobSearchState) -> JobSearchState:
    """Fetch job postings from RapidAPI."""
    logger.info("Node: fetch_jobs")
    try:
        jobs = await fetch_jobs(
            query=state["query"],
            location=state["location"],
            remote_only=state["remote_only"],
        )
        state["job_postings"] = jobs
    except Exception as e:
        logger.error(f"fetch_jobs failed: {e}")
        state["error"] = str(e)
        state["job_postings"] = []
    return state


# ── Node 2: Embed Resume ──────────────────────────────────────────────────────

async def node_embed_resume(state: JobSearchState) -> JobSearchState:
    """Embed the resume text."""
    logger.info("Node: embed_resume")
    try:
        resume = state["resume"]
        # Combine key resume fields for richer embedding
        resume_text = f"""
        Skills: {', '.join(resume.skills)}
        Job Titles: {', '.join(resume.job_titles)}
        Education: {', '.join(resume.education)}
        Summary: {resume.summary}
        """
        embedding = await embed_text(resume_text)
        state["resume_embedding"] = embedding
    except Exception as e:
        logger.error(f"embed_resume failed: {e}")
        state["error"] = str(e)
    return state


# ── Node 3: Embed Jobs ────────────────────────────────────────────────────────

async def node_embed_jobs(state: JobSearchState) -> JobSearchState:
    """Embed all job descriptions."""
    logger.info("Node: embed_jobs")
    try:
        jobs = state["job_postings"]
        if not jobs:
            state["job_embeddings"] = []
            return state

        texts = [f"{job.title} {job.company} {job.description}" for job in jobs]
        embeddings = await embed_texts(texts)
        state["job_embeddings"] = embeddings
    except Exception as e:
        logger.error(f"embed_jobs failed: {e}")
        state["error"] = str(e)
        state["job_embeddings"] = []
    return state


# ── Node 4: Match Jobs ────────────────────────────────────────────────────────

async def node_match_jobs(state: JobSearchState) -> JobSearchState:
    """Score and rank jobs by similarity to resume."""
    logger.info("Node: match_jobs")
    try:
        resume_embedding = state["resume_embedding"]
        job_embeddings = state["job_embeddings"]
        jobs = state["job_postings"]
        top_k = state["top_k"]

        # Compute cosine similarity for each job
        scored = []
        for job, job_emb in zip(jobs, job_embeddings):
            score = cosine_similarity(resume_embedding, job_emb)
            scored.append((job, score))

        # Sort by score descending and take top_k
        scored.sort(key=lambda x: x[1], reverse=True)
        top_jobs = scored[:top_k]

        # Build JobMatch objects (without cover letter yet)
        matches = []
        for job, score in top_jobs:
            match = JobMatch(
                job=job,
                match_score=round(score, 4),
                match_reasons=[],
                missing_skills=[],
            )
            matches.append(match)

        state["matches"] = matches
        logger.info(f"Top {len(matches)} matches found")
    except Exception as e:
        logger.error(f"match_jobs failed: {e}")
        state["error"] = str(e)
        state["matches"] = []
    return state


# ── Node 5: Analyze Matches ───────────────────────────────────────────────────

ANALYSIS_PROMPT = """
You are a job match analyzer. Given a resume summary and a job posting, return a JSON object with:
{{
  "match_reasons": ["reason1", "reason2", "reason3"],
  "missing_skills": ["skill1", "skill2"]
}}

- match_reasons: 3 specific reasons why this candidate matches this job
- missing_skills: skills mentioned in the job description that the candidate lacks

Resume:
Skills: {skills}
Job Titles: {job_titles}
Summary: {summary}

Job:
Title: {job_title}
Company: {company}
Description: {description}
"""


async def node_analyze_matches(state: JobSearchState) -> JobSearchState:
    """Use LLM to analyze why each job matches the resume."""
    logger.info("Node: analyze_matches")
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resume = state["resume"]

    analyzed = []
    for match in state["matches"]:
        try:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "user",
                        "content": ANALYSIS_PROMPT.format(
                            skills=", ".join(resume.skills),
                            job_titles=", ".join(resume.job_titles),
                            summary=resume.summary,
                            job_title=match.job.title,
                            company=match.job.company,
                            description=match.job.description[:1500],
                        )
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            data = json.loads(response.choices[0].message.content)
            match.match_reasons = data.get("match_reasons", [])
            match.missing_skills = data.get("missing_skills", [])
        except Exception as e:
            logger.warning(f"Analysis failed for job {match.job.job_id}: {e}")

        analyzed.append(match)

    state["matches"] = analyzed
    return state


# ── Node 6: Generate Cover Letters ───────────────────────────────────────────

COVER_LETTER_PROMPT = """
Write a professional cover letter for this candidate applying to this job.

Candidate:
- Name: Job Applicant
- Skills: {skills}
- Experience: {experience_years} years
- Previous titles: {job_titles}
- Summary: {summary}

Job:
- Title: {job_title}
- Company: {company}
- Description: {description}

Instructions:
- Keep it to 3 paragraphs
- Be specific about why the candidate fits this role
- Professional but personable tone
- Do NOT use placeholders like [Your Name]
"""


async def node_generate_cover_letters(state: JobSearchState) -> JobSearchState:
    """Generate a cover letter for each matched job."""
    logger.info("Node: generate_cover_letters")
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resume = state["resume"]

    for match in state["matches"]:
        try:
            response = await client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "user",
                        "content": COVER_LETTER_PROMPT.format(
                            skills=", ".join(resume.skills),
                            experience_years=resume.experience_years or 0,
                            job_titles=", ".join(resume.job_titles),
                            summary=resume.summary,
                            job_title=match.job.title,
                            company=match.job.company,
                            description=match.job.description[:1500],
                        )
                    }
                ],
                temperature=0.7,
            )
            match.cover_letter = response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Cover letter failed for job {match.job.job_id}: {e}")

    return state