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
from app.services.company_finder import search_company_careers_url, detect_ats_from_url
from app.extractors.factory import list_company_engineering_jobs
from app.extractors.linkedin import LinkedInExtractor
from app.config import settings
from fastapi import HTTPException

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
    result = await analyze_job_fit(str(req.url), req.resume_text)

    return JobFitResponse(**result)


@router.post("/linkedin-company-jobs", response_model=CompanyJobsResponse)
async def get_linkedin_company_jobs(req: JobUrlRequest):
    """
    Find engineering jobs from a company using a LinkedIn job posting URL.

    This endpoint:
    1. Normalizes the LinkedIn job URL
    2. Extracts the company name from the LinkedIn page
    3. Searches for the company's careers page or detects their ATS
    4. Returns all engineering jobs from that company

    Works with all supported ATS platforms: Ashby, Greenhouse, Lever, Workday, Rippling.

    Args:
        req: Request containing a LinkedIn job URL

    Returns:
        - company: The company name
        - total_jobs: The number of engineering jobs found
        - engineering_jobs: List of job listings with title, URL, and location
    """
    url = str(req.url)

    # Check if it's a LinkedIn URL
    if "linkedin.com/jobs" not in url:
        raise HTTPException(
            status_code=400,
            detail="URL must be a LinkedIn job posting (linkedin.com/jobs)",
        )

    # Extract company name from LinkedIn
    linkedin_extractor = LinkedInExtractor()
    company_name = linkedin_extractor.get_company_name(url)

    if not company_name:
        raise HTTPException(
            status_code=400,
            detail="Could not extract company name from LinkedIn job posting",
        )

    # Search for company careers page
    careers_url = await search_company_careers_url(company_name)

    if not careers_url:
        raise HTTPException(
            status_code=404,
            detail=f"Could not find careers page for {company_name}. "
            "The company may not use a supported ATS platform.",
        )

    # Detect ATS platform
    ats_platform = detect_ats_from_url(careers_url)

    if not ats_platform:
        raise HTTPException(
            status_code=400,
            detail=f"Found careers page for {company_name} at {careers_url}, "
            "but it doesn't use a supported ATS platform. "
            "Supported: Ashby, Greenhouse, Lever, Workday, Rippling",
        )

    # Use the existing list_company_engineering_jobs with the discovered URL
    company, jobs = list_company_engineering_jobs(careers_url)

    return {"company": company or company_name, "total_jobs": len(jobs), "engineering_jobs": jobs}
