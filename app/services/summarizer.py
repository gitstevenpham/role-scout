"""Job summarization service."""

from openai import AsyncOpenAI
from fastapi import HTTPException

from app.config import settings
from app.extractors import extract_job_description


JOB_SUMMARY_PROMPT = """Analyze the following job listing and return a structured summary.
Extract:
1. Job title
2. Company (if mentioned)
3. A brief summary of the role (2-3 sentences)
4. Required skills / qualifications (bulleted list)
5. Nice-to-have / preferred skills (bulleted list, if any)

Job listing content:
{content}"""


def get_llm_client() -> tuple[AsyncOpenAI, str]:
    """Get configured LLM client and model name."""
    if settings.llm_provider == "openai":
        return AsyncOpenAI(api_key=settings.openai_api_key), settings.openai_model
    return (
        AsyncOpenAI(base_url=settings.local_llm_base_url, api_key="not-needed"),
        settings.local_llm_model,
    )


async def summarize_job_from_url(url: str) -> str:
    """
    Extract and summarize a job listing from a URL.

    Args:
        url: Job listing URL

    Returns:
        Summarized job description

    Raises:
        HTTPException: If extraction or summarization fails
    """
    # Extract job description
    job_content = extract_job_description(url)

    if not job_content:
        raise HTTPException(
            status_code=400,
            detail="Unable to extract job description from the provided URL. "
            "Supported platforms: Ashby, Greenhouse, LinkedIn",
        )

    # Summarize using LLM
    client, model = get_llm_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": JOB_SUMMARY_PROMPT.format(content=job_content)}
        ],
    )

    return response.choices[0].message.content
