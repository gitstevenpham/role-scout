"""Service for finding company careers pages and detecting ATS platforms."""

from typing import Optional
import httpx
from bs4 import BeautifulSoup

from app.extractors.factory import EXTRACTORS


async def search_company_careers_url(company_name: str) -> Optional[str]:
    """
    Search for a company's careers/jobs page URL using web search.

    Args:
        company_name: The company name to search for

    Returns:
        The careers page URL or None if not found
    """
    try:
        # Try common careers page patterns first
        common_patterns = [
            f"https://{company_name.lower().replace(' ', '')}.com/careers",
            f"https://www.{company_name.lower().replace(' ', '')}.com/careers",
            f"https://{company_name.lower().replace(' ', '')}.com/jobs",
            f"https://careers.{company_name.lower().replace(' ', '')}.com",
            f"https://jobs.{company_name.lower().replace(' ', '')}.com",
        ]

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }

        # Test each pattern to see if it exists
        async with httpx.AsyncClient() as client:
            for pattern in common_patterns:
                try:
                    response = await client.get(
                        pattern, headers=headers, follow_redirects=True, timeout=5.0
                    )
                    if response.status_code == 200:
                        # Check if the page contains job-related content
                        soup = BeautifulSoup(response.text, "html.parser")
                        text_lower = soup.get_text().lower()
                        if any(
                            keyword in text_lower
                            for keyword in ["job", "career", "position", "opening"]
                        ):
                            return str(response.url)
                except (httpx.HTTPError, Exception):
                    continue

        return None

    except Exception as e:
        print(f"Error searching for company careers URL: {e}")
        return None


def detect_ats_from_url(url: str) -> Optional[str]:
    """
    Detect which ATS platform a careers page URL uses.

    Args:
        url: The careers page URL

    Returns:
        The ATS platform name (e.g., "ashby", "greenhouse", "lever") or None
    """
    url_lower = url.lower()

    # Check each extractor to see if it can handle this URL
    for extractor_class in EXTRACTORS:
        if extractor_class.can_handle(url):
            # Return the extractor class name without "Extractor"
            return extractor_class.__name__.replace("Extractor", "").lower()

    # Check for common ATS patterns in URL
    ats_patterns = {
        "ashby": ["ashbyhq.com", "jobs.ashbyhq.com"],
        "greenhouse": ["greenhouse.io", "boards.greenhouse.io"],
        "lever": ["lever.co", "jobs.lever.co"],
        "workday": ["myworkdayjobs.com"],
        "rippling": ["ats.rippling.com"],
        "linkedin": ["linkedin.com/jobs"],
    }

    for ats_name, patterns in ats_patterns.items():
        if any(pattern in url_lower for pattern in patterns):
            return ats_name

    return None
