import logging
from serpapi import GoogleSearch
from core.config import get_settings
from models.schemas import JobPosting
from services.text_utils import clean_job_description

logger = logging.getLogger(__name__)
settings = get_settings()


async def fetch_jobs_serpapi(
    query: str,
    location: str = "",
    num_results: int = 10,
) -> list[JobPosting]:
    """Fetch job postings from Google Jobs via SerpApi."""

    if not settings.serpapi_key:
        logger.warning("SERPAPI_KEY not set — skipping SerpApi")
        return []

    try:
        params = {
            "engine":   "google_jobs",
            "q":        f"{query} {location}".strip(),
            "hl":       "en",
            "api_key":  settings.serpapi_key,
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        jobs_data = results.get("jobs_results", [])

        jobs = []
        for item in jobs_data[:num_results]:
            try:
                # Extract salary if available
                salary_min = None
                salary_max = None
                detected_salary = item.get("detected_extensions", {})
                if "salary" in detected_salary:
                    salary_min = detected_salary.get("salary_min")
                    salary_max = detected_salary.get("salary_max")

                job = JobPosting(
                    job_id=         f"serpapi_{item.get('job_id', '')}",
                    title=          item.get("title", ""),
                    company=        item.get("company_name", ""),
                    location=       item.get("location", ""),
                    description=clean_job_description(item.get("description", "")),
                    apply_link=     item.get("related_links", [{}])[0].get("link") if item.get("related_links") else None,
                    posted_at=      item.get("detected_extensions", {}).get("posted_at"),
                    employment_type=item.get("detected_extensions", {}).get("schedule_type"),
                    salary_min=     salary_min,
                    salary_max=     salary_max,
                    remote=         "remote" in item.get("location", "").lower(),
                )
                jobs.append(job)
            except Exception as e:
                logger.warning(f"Skipping malformed SerpApi job: {e}")
                continue

        logger.info(f"SerpApi fetched {len(jobs)} jobs for query: '{query}'")
        return jobs

    except Exception as e:
        logger.error(f"SerpApi fetch failed: {e}")
        return []