"""API endpoint definitions."""

from fastapi import APIRouter

from app.schemas.job import JobUrlRequest, JobSummaryResponse, HealthResponse
from app.services.summarizer import summarize_job_from_url, get_llm_client
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
