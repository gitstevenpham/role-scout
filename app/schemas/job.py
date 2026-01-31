"""Pydantic schemas for job-related requests and responses."""

from pydantic import BaseModel, HttpUrl


class JobUrlRequest(BaseModel):
    """Request model for job URL."""

    url: HttpUrl


class JobSummaryResponse(BaseModel):
    """Response model for job summary."""

    url: str
    summary: str


class JobListing(BaseModel):
    """A single job listing."""

    title: str
    url: str
    location: str | None = None


class CompanyJobsResponse(BaseModel):
    """Response model for company job listings."""

    company: str
    total_jobs: int
    engineering_jobs: list[JobListing]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    provider: str
