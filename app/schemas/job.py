"""Pydantic schemas for job-related requests and responses."""

from pydantic import BaseModel, HttpUrl


class JobUrlRequest(BaseModel):
    """Request model for job URL."""

    url: HttpUrl


class JobSummaryResponse(BaseModel):
    """Response model for job summary."""

    url: str
    summary: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    provider: str
