"""Job fit analysis service."""

import re
from pathlib import Path

from fastapi import HTTPException
from pypdf import PdfReader

from app.config import settings
from app.extractors import extract_job_description
from app.services.summarizer import get_llm_client


JOB_FIT_PROMPT = """You are a career advisor helping a candidate understand if they're a good fit for a job.

CANDIDATE'S RESUME:
{resume}

JOB DESCRIPTION:
{job_description}

Please analyze how well this candidate matches the job requirements and provide a structured analysis in the following format:

FIT SCORE: [Choose one: "Strong Match" | "Moderate Match" | "Weak Match" | "Poor Match"]

RECOMMENDATION:
[Write 2-3 sentences with your overall recommendation on whether they should apply and what to emphasize]

MATCHING QUALIFICATIONS:
- [First matching qualification]
- [Second matching qualification]
- [Continue for all strong matches]

GAPS:
- [First gap or missing skill]
- [Second gap or missing skill]
- [Continue for all significant gaps]

DETAILED ANALYSIS:
[Write 2-3 paragraphs providing a thorough analysis of the fit, including specific examples from both the resume and job description]
"""

def load_resume_from_config() -> str:
    """
    Load resume from configured path.

    Returns:
        Resume text content

    Raises:
        HTTPException: If resume file not found, not configured, or empty
    """
    if not settings.resume_path:
        raise HTTPException(
            status_code=500,
            detail="Resume path not configured. Set RESUME_PATH in your .env file.",
        )

    resume_path = Path(settings.resume_path)

    if not resume_path.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Resume file not found at: {settings.resume_path}",
        )

    # Handle PDF files
    if resume_path.suffix.lower() == ".pdf":
        try:
            reader = PdfReader(str(resume_path))
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())
            resume_text = "\n\n".join(text_parts)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to parse PDF resume: {str(e)}",
            )
    else:
        # Handle text/markdown files
        try:
            resume_text = resume_path.read_text(encoding="utf-8")
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to read resume file: {str(e)}",
            )

    if not resume_text or not resume_text.strip():
        raise HTTPException(
            status_code=500,
            detail="Resume file is empty",
        )

    return resume_text


async def analyze_job_fit(url: str, resume_text: str | None = None) -> dict:
    """
    Analyze how well a job matches the candidate's resume.

    Args:
        url: Job listing URL
        resume_text: Optional resume text override (if None, loads from config)

    Returns:
        Dictionary with fit analysis

    Raises:
        HTTPException: If extraction or analysis fails
    """
    # Extract job description
    job_content = extract_job_description(url)

    if not job_content:
        raise HTTPException(
            status_code=400,
            detail="Unable to extract job description from the provided URL. "
            "Supported platforms: Ashby, Greenhouse, LinkedIn, Lever, Workday, Rippling",
        )

    # Load resume
    if resume_text is None:
        resume_text = load_resume_from_config()

    # Analyze fit using LLM
    client, model = get_llm_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": JOB_FIT_PROMPT.format(
                    resume=resume_text, job_description=job_content
                ),
            }
        ],
    )

    llm_response = response.choices[0].message.content

    return {
        "url": url,
        "analysis": llm_response,
    }
