import json
import logging
from openai import AsyncOpenAI
from services.openai_service import embed_text, embed_texts, cosine_similarity
from services.rapidapi_service import fetch_jobs
from models.schemas import JobMatch
from agents.state import JobSearchState
from core.config import get_settings
from services.serpapi_service import fetch_jobs_serpapi

from services.security import filter_llm_output

logger = logging.getLogger(__name__)
settings = get_settings()


# ── Node 1: Fetch Jobs ────────────────────────────────────────────────────────

async def node_fetch_jobs(state: JobSearchState) -> JobSearchState:
    """Fetch job postings from multiple sources and combine them."""
    logger.info("Node: fetch_jobs")
    try:
        query      = state["query"]
        location   = state["location"]
        remote_only = state["remote_only"]

        # ── Source 1: RapidAPI ─────────────────────────────────────────────
        logger.info("Fetching from RapidAPI...")
        rapidapi_jobs = await fetch_jobs(
            query=query,
            location=location,
            remote_only=remote_only,
        )

        # ── Source 2: SerpApi ──────────────────────────────────────────────
        logger.info("Fetching from SerpApi...")
        serpapi_jobs = await fetch_jobs_serpapi(
            query=query,
            location=location,
            num_results=10,
        )

        # ── Combine + deduplicate by title+company ─────────────────────────
        all_jobs = rapidapi_jobs + serpapi_jobs
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = f"{job.title.lower()}_{job.company.lower()}"
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        logger.info(
            f"Total jobs: {len(unique_jobs)} "
            f"(RapidAPI={len(rapidapi_jobs)}, "
            f"SerpApi={len(serpapi_jobs)}, "
            f"duplicates removed={len(all_jobs) - len(unique_jobs)})"
        )

        state["job_postings"] = unique_jobs

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

def extract_job_skills(job_description: str) -> list[str]:
    """Extract required skills mentioned in job description."""
    job_desc_lower = job_description.lower()

    # Common skills to look for in job descriptions
    known_skills = [
        # Cybersecurity
        "burp suite", "nmap", "sqlmap", "wireshark", "metasploit",
        "kali linux", "penetration testing", "vulnerability assessment",
        "siem", "splunk", "qradar", "firewall", "ids", "ips",
        "incident response", "threat intelligence", "ethical hacking",
        "network security", "information security", "cybersecurity",
        "log analysis", "forensics", "malware analysis",
        # Programming
        "python", "java", "javascript", "c++", "c#", "go", "rust",
        "html", "css", "sql", "bash", "powershell",
          # Cloud
        "aws", "azure", "gcp", "docker", "kubernetes",
        # OS
        "linux", "unix", "windows", "macos",
        # General
        "git", "rest api", "machine learning", "deep learning",
        "data analysis", "problem solving", "communication",
    ]

    found = [skill for skill in known_skills if skill in job_desc_lower]
    return found


def calculate_skill_overlap(resume_skills: list[str], job_description: str) -> float:
    """
    Calculate what % of job required skills the candidate has.
    CORRECT formula: candidate_has / job_requires
    """
    if not resume_skills or not job_description:
        return 0.0

    # Step 1: Extract what job requires
    job_required_skills = extract_job_skills(job_description)

    if not job_required_skills:
        return 0.5   # no specific skills mentioned → neutral score

    # Step 2: Check how many job skills candidate has
    resume_lower = [s.lower() for s in resume_skills]

    # Skill aliases for fuzzy matching
    skill_aliases = {
        "burp suite":           ["burp suite", "burp"],
        "nmap":                 ["nmap", "network scanning"],
        "penetration testing":  ["penetration testing", "pentest", "pen test", "ethical hacking"],
        "vulnerability assessment": ["vulnerability assessment", "vuln assessment"],
        "siem":                 ["siem", "security information"],
        "incident response":    ["incident response", "ir"],
        "network security":     ["network security", "networking"],
        "linux":                ["linux", "linux environment", "kali", "ubuntu"],
        "python":               ["python", "python3"],
        "information security": ["information security", "infosec", "cybersecurity"],
        "firewall":             ["firewall", "firewall management", "firewall configuration"],
        "log analysis":         ["log analysis", "siem", "splunk"],
        "ethical hacking":      ["ethical hacking", "penetration testing", "pentest"],
        "threat intelligence":  ["threat intelligence", "threat analysis"],
    }

    matched = 0
    for job_skill in job_required_skills:
        # Check direct match
        if job_skill in resume_lower:
            matched += 1
            continue

        # Check aliases
        aliases = skill_aliases.get(job_skill, [job_skill])
        if any(alias in " ".join(resume_lower) for alias in aliases):
            matched += 1
            continue

    score = matched / len(job_required_skills)

    logger.info(
        f"Skill overlap: {matched}/{len(job_required_skills)} "
        f"job skills matched = {score:.2f}"
    )

    return score


def calculate_seniority_score(experience_years: float, job_description: str) -> float:
    """Score how well candidate's experience level matches job requirements."""
    job_desc_lower = job_description.lower()

    # Detect seniority signals in job description
    senior_signals   = ["senior", "lead", "principal", "5+ years", "7+ years", "10+ years"]
    mid_signals      = ["mid", "3+ years", "4+ years", "3-5 years", "2-4 years"]
    junior_signals   = ["junior", "entry", "fresher", "0-2 years", "1-2 years", "graduate"]

    is_senior = any(s in job_desc_lower for s in senior_signals)
    is_mid    = any(s in job_desc_lower for s in mid_signals)
    is_junior = any(s in job_desc_lower for s in junior_signals)

    # Score based on candidate experience vs job level
    if experience_years <= 2:        # junior candidate
        if is_junior: return 1.0
        if is_mid:    return 0.5
        if is_senior: return 0.2
        return 0.7   # no signal found — neutral

    elif experience_years <= 5:      # mid candidate
        if is_mid:    return 1.0
        if is_junior: return 0.7
        if is_senior: return 0.5
        return 0.8

    else:                            # senior candidate
        if is_senior: return 1.0
        if is_mid:    return 0.8
        if is_junior: return 0.5
        return 0.9


async def node_match_jobs(state: JobSearchState) -> JobSearchState:
    """Score and rank jobs using hybrid scoring:
    50% semantic similarity + 30% skill overlap + 20% seniority match
    """
    logger.info("Node: match_jobs")
    try:
        resume_embedding  = state["resume_embedding"]
        job_embeddings    = state["job_embeddings"]
        jobs              = state["job_postings"]
        top_k             = state["top_k"]
        resume            = state["resume"]

        scored = []
        for job, job_emb in zip(jobs, job_embeddings):

            # Score 1: Semantic similarity (FAISS cosine)
            semantic_score = cosine_similarity(resume_embedding, job_emb)

            # Score 2: Skill overlap
            skill_score = calculate_skill_overlap(
                resume.skills,
                job.description
            )

            # Score 3: Seniority match
            seniority_score = calculate_seniority_score(
                resume.experience_years or 0,
                job.description
            )

            # Hybrid final score
            final_score = (
                semantic_score  * 0.5 +
                skill_score     * 0.3 +
                seniority_score * 0.2
            )

            logger.info(
                f"Job: {job.title[:30]} | "
                f"semantic={semantic_score:.2f} "
                f"skill={skill_score:.2f} "
                f"seniority={seniority_score:.2f} "
                f"final={final_score:.2f}"
            )

            scored.append((job, final_score))

        # Sort highest to lowest and take top_k
        scored.sort(key=lambda x: x[1], reverse=True)
        top_jobs = scored[:top_k]

        # Build JobMatch objects
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
You are an expert technical recruiter analyzing a candidate-job fit.
Be specific and actionable — reference exact skills, tools, and experience.

Return ONLY valid JSON:
{{
  "match_reasons": ["reason1", "reason2", "reason3"],
  "missing_skills": ["skill1", "skill2"],
  "match_summary": "one sentence overall assessment"
}}

Rules:
- match_reasons: exactly 3 reasons, each must mention SPECIFIC skills or tools
  BAD: "candidate has cybersecurity experience"
  GOOD: "Burp Suite and Nmap experience directly matches vulnerability assessment requirements"
- missing_skills: only skills explicitly mentioned in job description that candidate lacks
  Format each as: "SkillName — why it matters for this role"
  e.g. "Splunk — required for SIEM monitoring mentioned 3x in JD"
- match_summary: one honest sentence about overall fit
  e.g. "Strong junior fit — 80% skill overlap but lacks enterprise SIEM experience"
- Maximum 5 missing skills — only the most critical ones

Candidate Profile:
Skills: {skills}
Job Titles: {job_titles}
Experience: {experience_years} years
Seniority: {seniority}
Summary: {summary}

Job Posting:
Title: {job_title}
Company: {company}
Description: {description}
"""


async def node_analyze_matches(state: JobSearchState) -> JobSearchState:
    """Use LLM to analyze why each job matches the resume."""
    logger.info("Node: analyze_matches")
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resume = state["resume"]

    # Extract seniority from summary
    seniority = "junior"
    if "[JUNIOR" in resume.summary:
        seniority = "junior"
    elif "[MID" in resume.summary:
        seniority = "mid"
    elif "[SENIOR" in resume.summary:
        seniority = "senior"

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
                            experience_years=resume.experience_years or 0,
                            seniority=seniority,
                            summary=resume.summary,
                            job_title=match.job.title,
                            company=match.job.company,
                            description=match.job.description[:2000],
                        )
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            data = json.loads(response.choices[0].message.content)
            match.match_reasons  = data.get("match_reasons", [])
            match.missing_skills = data.get("missing_skills", [])

            # Log the match summary
            logger.info(f"Match summary for {match.job.title[:30]}: {data.get('match_summary', '')}")

        except Exception as e:
            logger.warning(f"Analysis failed for job {match.job.job_id}: {e}")

        analyzed.append(match)

    state["matches"] = analyzed
    return state


# ── Node 6: Generate Cover Letters ───────────────────────────────────────────

COVER_LETTER_PROMPT = """
Write a professional cover letter for this candidate applying to this job.

Candidate:
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
- Start directly with "Dear Hiring Manager," — no address block, no date, no placeholders
- End with "Sincerely," followed by a blank line — no name placeholder
- Do NOT include [Your Name], [Your Address], [Date] or any placeholders
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
            raw_output = response.choices[0].message.content
            clean_output, warnings = filter_llm_output(raw_output, source="cover letter")
            if warnings:
                logger.warning(f"Cover letter filtered: {warnings}")
            match.cover_letter = clean_output
            
        except Exception as e:
            logger.warning(f"Cover letter failed for job {match.job.job_id}: {e}")

    return state