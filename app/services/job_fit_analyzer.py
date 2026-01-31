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

JOB TITLE: [Extract the job title]
COMPANY: [Extract the company name]
FIT SCORE: [Choose one: "Strong Match" | "Moderate Match" | "Weak Match" | "Poor Match"]

MATCHING QUALIFICATIONS:
- [First matching qualification]
- [Second matching qualification]
- [Continue for all strong matches]

GAPS:
- [First gap or missing skill]
- [Second gap or missing skill]
- [Continue for all significant gaps]

RECOMMENDATION:
[Write 2-3 sentences with your overall recommendation on whether they should apply and what to emphasize]

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


def parse_fit_analysis(llm_response: str) -> dict:
    """
    Parse structured LLM response into dictionary.

    Args:
        llm_response: Raw LLM response text

    Returns:
        Dictionary with parsed sections

    Raises:
        HTTPException: If parsing fails
    """
    try:
        # Extract job title
        job_title_match = re.search(
            r"JOB TITLE:\s*(.+?)(?:\n|$)", llm_response, re.IGNORECASE
        )
        job_title = job_title_match.group(1).strip() if job_title_match else "Unknown"

        # Extract company
        company_match = re.search(
            r"COMPANY:\s*(.+?)(?:\n|$)", llm_response, re.IGNORECASE
        )
        company = company_match.group(1).strip() if company_match else "Unknown"

        # Extract fit score
        fit_score_match = re.search(
            r"FIT SCORE:\s*(.+?)(?:\n|$)", llm_response, re.IGNORECASE
        )
        fit_score = (
            fit_score_match.group(1).strip() if fit_score_match else "Moderate Match"
        )

        # Extract matching qualifications
        matching_section = re.search(
            r"MATCHING QUALIFICATIONS:\s*\n((?:[-•*]\s*.+\n?)+)",
            llm_response,
            re.IGNORECASE,
        )
        matching_qualifications = []
        if matching_section:
            matches = re.findall(r"[-•*]\s*(.+)", matching_section.group(1))
            matching_qualifications = [m.strip() for m in matches]

        # Extract gaps
        gaps_section = re.search(
            r"GAPS:\s*\n((?:[-•*]\s*.+\n?)+)", llm_response, re.IGNORECASE
        )
        gaps = []
        if gaps_section:
            gap_matches = re.findall(r"[-•*]\s*(.+)", gaps_section.group(1))
            gaps = [g.strip() for g in gap_matches]

        # Extract recommendation
        recommendation_match = re.search(
            r"RECOMMENDATION:\s*\n(.+?)(?=\n\n|\nDETAILED ANALYSIS:|\Z)",
            llm_response,
            re.IGNORECASE | re.DOTALL,
        )
        recommendation = (
            recommendation_match.group(1).strip()
            if recommendation_match
            else "Apply if interested."
        )

        # Extract detailed analysis
        detailed_match = re.search(
            r"DETAILED ANALYSIS:\s*\n(.+)", llm_response, re.IGNORECASE | re.DOTALL
        )
        detailed_analysis = (
            detailed_match.group(1).strip()
            if detailed_match
            else "Analysis not available."
        )

        return {
            "job_title": job_title,
            "company": company,
            "fit_score": fit_score,
            "matching_qualifications": matching_qualifications,
            "gaps": gaps,
            "recommendation": recommendation,
            "detailed_analysis": detailed_analysis,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse LLM response: {str(e)}",
        )


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

    # Parse LLM response
    analysis = parse_fit_analysis(llm_response)

    # Add the URL to the result
    analysis["url"] = url

    return analysis
