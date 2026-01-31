from typing import Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseJobExtractor


class LinkedInExtractor(BaseJobExtractor):
    """Extractor for LinkedIn job listings."""

    @staticmethod
    def can_handle(url: str) -> bool:
        """Check if URL is a LinkedIn job listing."""
        return "linkedin.com/jobs" in url

    def extract(self, url: str) -> Optional[str]:
        """Extract job description from LinkedIn job listing."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }

            with httpx.Client() as client:
                response = client.get(
                    url, headers=headers, follow_redirects=True, timeout=10.0
                )
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # LinkedIn uses specific classes for job description
            job_content = soup.find("div", class_="description__text")
            if not job_content:
                job_content = soup.find(
                    "div", class_=lambda x: x and "show-more-less-html__markup" in str(x)
                )

            if not job_content:
                # Try alternative selectors
                job_content = soup.find("section", class_=lambda x: x and "description" in str(x))

            if job_content:
                return job_content.get_text(separator="\n", strip=True)

            return None

        except Exception as e:
            print(f"Error extracting LinkedIn job: {e}")
            return None
