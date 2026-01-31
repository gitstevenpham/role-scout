from typing import Optional
import httpx
from bs4 import BeautifulSoup

from .base import BaseJobExtractor


class GreenhouseExtractor(BaseJobExtractor):
    """Extractor for Greenhouse ATS job listings."""

    @staticmethod
    def can_handle(url: str) -> bool:
        """Check if URL is a Greenhouse job listing."""
        return "greenhouse.io" in url or "boards.greenhouse.io" in url

    def extract(self, url: str) -> Optional[str]:
        """Extract job description from Greenhouse job listing."""
        try:
            with httpx.Client() as client:
                response = client.get(url, follow_redirects=True, timeout=10.0)
                response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Greenhouse uses specific div IDs for job content
            job_content = soup.find("div", {"id": "content"})
            if not job_content:
                job_content = soup.find("div", class_="application")

            if not job_content:
                # Try to find the main content section
                job_content = soup.find("section", class_=lambda x: x and "job" in x.lower())

            if job_content:
                # Remove application form if present
                for form in job_content.find_all("form"):
                    form.decompose()

                return job_content.get_text(separator="\n", strip=True)

            return None

        except Exception as e:
            print(f"Error extracting Greenhouse job: {e}")
            return None
