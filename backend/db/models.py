from sqlalchemy import Column, String, Float, DateTime, Text, JSON
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from datetime import datetime
from core.config import get_settings

settings = get_settings()


# ── Base ──────────────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ── Resume Table ──────────────────────────────────────────────────────────────
class ResumeDB(Base):
    __tablename__ = "resumes"

    resume_id       = Column(String, primary_key=True)
    raw_text        = Column(Text, nullable=False)
    skills          = Column(JSON, nullable=False, default=list)
    experience_years= Column(Float, nullable=True)
    education       = Column(JSON, nullable=False, default=list)
    job_titles      = Column(JSON, nullable=False, default=list)
    summary         = Column(Text, nullable=False)
    chunk_count     = Column(Float, nullable=False, default=1)
    embedding       = Column(JSON, nullable=True)   # stored as list of floats
    created_at      = Column(DateTime, default=datetime.utcnow)


# ── Job Search Table ──────────────────────────────────────────────────────────
class JobSearchDB(Base):
    __tablename__ = "job_searches"

    search_id           = Column(String, primary_key=True)
    resume_id           = Column(String, nullable=False)
    query               = Column(String, nullable=False)
    location            = Column(String, nullable=True)
    remote_only         = Column(String, nullable=False, default="false")
    top_k               = Column(Float, nullable=False, default=5)
    total_jobs_fetched  = Column(Float, nullable=False, default=0)
    created_at          = Column(DateTime, default=datetime.utcnow)


# ── Job Match Table ───────────────────────────────────────────────────────────
class JobMatchDB(Base):
    __tablename__ = "job_matches"

    match_id        = Column(String, primary_key=True)
    search_id       = Column(String, nullable=False)
    job_id          = Column(String, nullable=False)
    title           = Column(String, nullable=False)
    company         = Column(String, nullable=False)
    location        = Column(String, nullable=True)
    source          = Column(String, nullable=True)
    apply_link      = Column(String, nullable=True)
    match_score     = Column(Float, nullable=False)
    match_reasons   = Column(JSON, nullable=False, default=list)
    missing_skills  = Column(JSON, nullable=False, default=list)
    cover_letter    = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)


# ── Database Engine ───────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.database_url,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency to get database session."""
    async with AsyncSessionLocal() as session:
        yield session