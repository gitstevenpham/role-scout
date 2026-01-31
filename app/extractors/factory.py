from typing import Optional

from .ashby import AshbyExtractor
from .greenhouse import GreenhouseExtractor
from .linkedin import LinkedInExtractor
from .lever import LeverExtractor
from .workday import WorkdayExtractor
from .rippling import RipplingExtractor
from .generic import GenericExtractor
from .base import BaseJobExtractor
from app.schemas.job import JobListing
from app.utils.filters import is_engineering_role


EXTRACTORS: list[type[BaseJobExtractor]] = [
    AshbyExtractor,
    GreenhouseExtractor,
    LinkedInExtractor,
    LeverExtractor,
    WorkdayExtractor,
    RipplingExtractor,
    GenericExtractor,  # Fallback extractor - must be last
]


def extract_job_description(url: str) -> Optional[str]:
    """
    Extract job description from a URL by detecting the appropriate ATS.

    Args:
        url: The job listing URL

    Returns:
        Extracted job description text, or None if extraction fails
    """
    for extractor_class in EXTRACTORS:
        if extractor_class.can_handle(url):
            extractor = extractor_class()
            return extractor.extract(url)

    return None


def list_company_engineering_jobs(
    url: str
) -> tuple[str, list[JobListing]]:
    """
    List engineering jobs from the same company as the given job URL.

    Args:
        url: The job listing URL
        limit: Maximum number of jobs to return (default: 20)

    Returns:
        Tuple of (company_name, list of JobListing Pydantic models)
    """
    # Find the appropriate extractor
    for extractor_class in EXTRACTORS:
        if extractor_class.can_handle(url):
            extractor = extractor_class()

            # Get all company jobs (returns base.JobListing objects)
            company_name, all_jobs = extractor.list_company_jobs(url)

            # Filter for engineering roles and convert to Pydantic models
            engineering_jobs = [
                JobListing(title=job.title, url=job.url, location=job.location)
                for job in all_jobs
                if is_engineering_role(job.title)
            ]

            # Limit the results
            limited_jobs = engineering_jobs

            return (company_name, limited_jobs)

    # No suitable extractor found
    return ("Unknown", [])
