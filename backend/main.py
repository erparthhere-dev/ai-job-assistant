import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import get_settings
from models.schemas import ResumeParseResponse, ErrorResponse
from services.resume_service import parse_resume, get_resume

from agents.graph import job_search_graph
from models.schemas import JobSearchRequest, JobSearchResponse
from services.resume_service import get_resume

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ── App lifecycle ─────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 AI Job Assistant API starting up...")
    yield
    logger.info("👋 AI Job Assistant API shutting down...")


# ── App init ──────────────────────────────────────────────────────────────────
settings = get_settings()

app = FastAPI(
    title="AI Job Application Assistant",
    description="Upload your resume and get matched with the best jobs + personalized cover letters.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}


# ── Resume endpoints ──────────────────────────────────────────────────────────

@app.post(
    "/api/resume/upload",
    response_model=ResumeParseResponse,
    tags=["Resume"],
    summary="Upload and parse a resume PDF",
)
async def upload_resume(
    file: UploadFile = File(..., description="PDF resume file"),
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_bytes = await file.read()

    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum size is 10MB.")

    if len(file_bytes) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        result = await parse_resume(file_bytes, file.filename)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Resume parsing failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to parse resume. Please try again.")


@app.get(
    "/api/resume/{resume_id}",
    response_model=ResumeParseResponse,
    tags=["Resume"],
    summary="Retrieve a previously parsed resume",
)
async def get_resume_by_id(resume_id: str):
    resume = get_resume(resume_id)
    if not resume:
        raise HTTPException(status_code=404, detail=f"Resume '{resume_id}' not found.")
    return resume

# ── Job Search endpoint ───────────────────────────────────────────────────────

@app.post(
    "/api/jobs/search",
    response_model=JobSearchResponse,
    tags=["Jobs"],
    summary="Match resume to jobs and generate cover letters",
)
async def search_jobs(request: JobSearchRequest):
    """
    Given a resume ID, fetch matching jobs and generate cover letters.
    """
    # Get the parsed resume
    resume = get_resume(request.resume_id)
    if not resume:
        raise HTTPException(
            status_code=404,
            detail=f"Resume '{request.resume_id}' not found. Please upload your resume first."
        )

    # Build initial state
    initial_state: dict = {
        "resume": resume,
        "query": request.query or " ".join(resume.job_titles) or "software engineer",
        "location": request.location or "",
        "remote_only": request.remote_only,
        "top_k": request.top_k,
        "job_postings": [],
        "resume_embedding": [],
        "job_embeddings": [],
        "matches": [],
        "error": None,
    }

    # Run the LangGraph workflow
    try:
        final_state = await job_search_graph.ainvoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Job search failed: {str(e)}")

    if final_state.get("error"):
        raise HTTPException(status_code=500, detail=final_state["error"])

    return JobSearchResponse(
        resume_id=request.resume_id,
        total_jobs_fetched=len(final_state["job_postings"]),
        matches=final_state["matches"],
    )

# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred.", "error_code": "INTERNAL_ERROR"},
    )


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.app_port, reload=True)