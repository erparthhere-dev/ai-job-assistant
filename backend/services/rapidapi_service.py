import logging
import httpx
from core.config import get_settings
from models.schemas import JobPosting

logger = logging.getLogger(__name__)
settings = get_settings()


async def fetch_jobs(
    query: str,
    location: str = "",
    remote_only: bool = False,
    num_pages: int = 1,
) -> list[JobPosting]:
    """Fetch job postings from RapidAPI JSearch."""

    url = "https://jsearch.p.rapidapi.com/search"

    params = {
        "query": f"{query} {location}".strip(),
        "page": "1",
        "num_pages": str(num_pages),
        "remote_jobs_only": "true" if remote_only else "false",
    }

    headers = {
        "X-RapidAPI-Key": settings.rapidapi_key,
        "X-RapidAPI-Host": settings.rapidapi_host,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

    jobs = []
    for item in data.get("data", []):
        try:
            job = JobPosting(
                job_id=item.get("job_id", ""),
                title=item.get("job_title", ""),
                company=item.get("employer_name", ""),
                location=f"{item.get('job_city', '')} {item.get('job_country', '')}".strip(),
                description=item.get("job_description", "")[:3000],  # truncate
                apply_link=item.get("job_apply_link"),
                posted_at=item.get("job_posted_at_datetime_utc"),
                employment_type=item.get("job_employment_type"),
                salary_min=item.get("job_min_salary"),
                salary_max=item.get("job_max_salary"),
                remote=item.get("job_is_remote", False),
            )
            jobs.append(job)
        except Exception as e:
            logger.warning(f"Skipping malformed job entry: {e}")
            continue

    logger.info(f"Fetched {len(jobs)} jobs for query: '{query}'")
    return jobs