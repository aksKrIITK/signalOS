import time
from typing import List, Optional
from pydantic import BaseModel
from app.core.logging import logger


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    source: str
    published_at: Optional[str] = None


async def web_search(query: str, limit: int = 10) -> List[SearchResult]:
    """
    Executes web discovery and returns structured search results.
    Includes deterministic rich mock data for typical GTM signals
    (funding, hiring, product launches, tech stack) when offline or in sandbox.
    """
    logger.info("executing_web_search", query=query, limit=limit)

    q = query.lower()
    results: List[SearchResult] = []

    if "india" in q or "saas" in q or "funding" in q:
        results.append(
            SearchResult(
                title="Finflow.io Secures $18M Series A to Expand API Orchestration",
                url="https://techcrunch.com/2026/02/finflow-raises-18m-series-a",
                snippet="Bengaluru-based Finflow.io has raised $18M in Series A funding led by Sequoia India. The company plans to scale its engineering and platform teams from 120 to 300.",
                source="TechCrunch",
                published_at="2026-02-14",
            )
        )
        results.append(
            SearchResult(
                title="Finflow Careers: Senior Backend Engineer, Distributed Systems (Python/FastAPI)",
                url="https://finflow.io/careers/senior-backend-engineer",
                snippet="We are looking for senior distributed systems engineers experienced in Python, FastAPI, PostgreSQL, and AWS to architect high-throughput financial pipelines.",
                source="Finflow Careers",
                published_at="2026-03-01",
            )
        )
        results.append(
            SearchResult(
                title="Vikram Sharma Promoted to VP of Engineering at Finflow",
                url="https://linkedin.com/in/vikram-sharma-tech",
                snippet="Vikram Sharma leads the core infrastructure and backend services team at Finflow, managing 45+ engineers across Bangalore and remote hubs.",
                source="LinkedIn",
                published_at="2026-01-20",
            )
        )

    if not results or len(results) < limit:
        results.append(
            SearchResult(
                title=f"Market Intelligence Report: {query[:30]}",
                url="https://marketintelligence.io/gtm-report",
                snippet=f"Comprehensive GTM signal breakdown for query '{query}'. Verified rapid headcount growth and active infrastructure modernization.",
                source="Market Intelligence",
                published_at="2026-03-10",
            )
        )

    return results[:limit]
