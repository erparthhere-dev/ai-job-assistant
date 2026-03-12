import logging
from langgraph.graph import StateGraph, END
from agents.state import JobSearchState
from agents.nodes import (
    node_fetch_jobs,
    node_embed_resume,
    node_embed_jobs,
    node_match_jobs,
    node_analyze_matches,
    node_generate_cover_letters,
)

logger = logging.getLogger(__name__)


def build_job_search_graph():
    """Build and compile the LangGraph job search workflow."""

    graph = StateGraph(JobSearchState)

    # ── Add nodes ─────────────────────────────────────────────────────────────
    graph.add_node("fetch_jobs", node_fetch_jobs)
    graph.add_node("embed_resume", node_embed_resume)
    graph.add_node("embed_jobs", node_embed_jobs)
    graph.add_node("match_jobs", node_match_jobs)
    graph.add_node("analyze_matches", node_analyze_matches)
    graph.add_node("generate_cover_letters", node_generate_cover_letters)

    # ── Define edges (flow) ───────────────────────────────────────────────────
    graph.set_entry_point("fetch_jobs")
    graph.add_edge("fetch_jobs", "embed_resume")
    graph.add_edge("embed_resume", "embed_jobs")
    graph.add_edge("embed_jobs", "match_jobs")
    graph.add_edge("match_jobs", "analyze_matches")
    graph.add_edge("analyze_matches", "generate_cover_letters")
    graph.add_edge("generate_cover_letters", END)

    compiled = graph.compile()
    logger.info("LangGraph job search workflow compiled successfully")
    return compiled


# Singleton instance
job_search_graph = build_job_search_graph()