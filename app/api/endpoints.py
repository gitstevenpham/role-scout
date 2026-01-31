"""API endpoint definitions."""

from fastapi import APIRouter

from app.schemas.job import (
    JobUrlRequest,
    JobSummaryResponse,
    HealthResponse,
    CompanyJobsResponse,
    JobFitRequest,
    JobFitResponse,
)
from app.services.summarizer import summarize_job_from_url
from app.services.job_fit_analyzer import analyze_job_fit
from app.extractors.factory import list_company_engineering_jobs
from app.config import settings

router = APIRouter()


@router.get("/", response_model=HealthResponse)
async def health():
    """Health check endpoint."""
    return {"status": "ok", "provider": settings.llm_provider}



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
    company, jobs = list_company_engineering_jobs(str(req.url))
    return {"company": company, "total_jobs": len(jobs), "engineering_jobs": jobs}


@router.post("/analyze-job-fit", response_model=JobFitResponse)
async def analyze_job_fit_endpoint(req: JobFitRequest):
    """
    Analyze how well a job matches the candidate's resume.

    Compares job description against resume and provides fit analysis including:
    - Fit score (Strong/Moderate/Weak/Poor Match)
    - Matching qualifications
    - Skills gaps
    - Application recommendation
    - Detailed analysis

    Supports all ATS platforms: Ashby, Greenhouse, LinkedIn, Lever, Workday, Rippling

    The resume is loaded from the path configured in RESUME_PATH environment variable,
    or you can provide resume_text in the request body to override.
    """
    analysis = await analyze_job_fit(str(req.url), req.resume_text)
    return JobFitResponse(**analysis)
