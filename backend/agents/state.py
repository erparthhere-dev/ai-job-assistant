from typing import Optional, TypedDict
from models.schemas import JobPosting, JobMatch, ResumeParseResponse


class JobSearchState(TypedDict):
    """
    Shared state passed between all LangGraph nodes.
    Each node reads from and writes to this state.
    """
    # Input
    resume: ResumeParseResponse
    query: str
    location: str
    remote_only: bool
    top_k: int

    # Intermediate
    job_postings: list[JobPosting]        # Raw jobs from RapidAPI
    resume_embedding: list[float]         # Embedded resume text
    job_embeddings: list[list[float]]     # Embedded job descriptions

    # Output
    matches: list[JobMatch]               # Scored + ranked matches
    error: Optional[str]                  # Any error message

    