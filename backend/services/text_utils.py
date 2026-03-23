import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def clean_html(text: str) -> str:
    """Remove HTML tags and clean up whitespace from text."""
    if not text:
        return ""

    # Parse and strip HTML tags
    soup = BeautifulSoup(text, "html.parser")
    cleaned = soup.get_text(separator=" ")

    # Remove extra whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()

    # Remove common HTML entities that might remain
    cleaned = cleaned.replace("&amp;", "&")
    cleaned = cleaned.replace("&nbsp;", " ")
    cleaned = cleaned.replace("&lt;", "<")
    cleaned = cleaned.replace("&gt;", ">")
    cleaned = cleaned.replace("&quot;", '"')

    return cleaned


def clean_job_description(description: str) -> str:
    """Clean a job description for use in embeddings and skill matching."""
    if not description:
        return ""

    cleaned = clean_html(description)

    # Truncate to 3000 characters
    if len(cleaned) > 3000:
        cleaned = cleaned[:3000] + "..."

    logger.debug(f"Cleaned description: {len(description)} → {len(cleaned)} chars")
    return cleaned