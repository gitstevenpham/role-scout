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

            # Greenhouse uses job-post-container class
            job_content = soup.find("div", class_="job-post-container")

            if job_content:
                # Remove application form and other non-job-description elements
                for form in job_content.find_all("form"):
                    form.decompose()
                for app in job_content.find_all("div", {"id": "application"}):
                    app.decompose()

                return job_content.get_text(separator="\n", strip=True)

            return None

        except Exception as e:
            print(f"Error extracting Greenhouse job: {e}")
            return None
