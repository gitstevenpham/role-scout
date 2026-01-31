"""API endpoint definitions."""

from fastapi import APIRouter

from app.schemas.job import (
    JobUrlRequest,
    JobSummaryResponse,
    HealthResponse,
    CompanyJobsResponse,
)
from app.services.summarizer import summarize_job_from_url, get_llm_client
from app.extractors.factory import list_company_engineering_jobs
from app.config import settings

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return {"status": "ok", "provider": settings.llm_provider}


@router.post("/chat")
async def chat(message: str = "hello world"):
    """Simple chat endpoint for testing LLM."""
    client, model = get_llm_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": message}],
    )
    return {
        "provider": settings.llm_provider,
        "model": model,
        "message": message,
        "reply": response.choices[0].message.content,
    }


@router.post("/summarize-job", response_model=JobSummaryResponse)
async def summarize_job(req: JobUrlRequest):
    """
    Extract and summarize a job listing from a URL.

    Supports:
    - Ashby (ashbyhq.com)
    - Greenhouse (greenhouse.io)
    - LinkedIn (linkedin.com/jobs)
    """
    summary = await summarize_job_from_url(str(req.url))
    return {"url": str(req.url), "summary": summary}


@router.post("/company-engineering-jobs", response_model=CompanyJobsResponse)
async def get_company_engineering_jobs(req: JobUrlRequest):
    """
    Find other software engineering jobs from the same company.

    Takes a URL of a single job listing, identifies the company, and returns
    up to 20 other software engineering job listings from that company.

    Supports:
    - Ashby (ashbyhq.com)
    - Greenhouse (greenhouse.io)
    - Lever (lever.co)
    - Workday (myworkdayjobs.com)
    - Rippling (ats.rippling.com)

    Returns:
    - company: The company name
    - total_jobs: The number of engineering jobs found
    - engineering_jobs: List of job listings with title, URL, and location
    """
    company, jobs = list_company_engineering_jobs(str(req.url), limit=20)
    return {"company": company, "total_jobs": len(jobs), "engineering_jobs": jobs}
